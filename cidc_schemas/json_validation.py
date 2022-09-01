# -*- encoding: utf-8 -*-

"""Tools for performing validations based on json schemas"""

import os
import copy
import functools
import json
import collections.abc
from contextlib import contextmanager
from typing import Optional, Callable, Union

import dateparser
from deepdiff import DeepSearch
import jsonschema
from jsonschema.exceptions import ValidationError, RefResolutionError
from jsonpointer import resolve_pointer

from .constants import SCHEMA_DIR, METASCHEMA_PATH
from .util import JSON


class InDocRefNotFoundError(ValidationError):
    pass


def _in_doc_refs_check(validator, schema_prop_value, ref_value, subschema):
    """A "dummy" validator, that just produces errors for every occurrence of `in_doc_ref_pattern`"""
    yield InDocRefNotFoundError(
        f"Ref {schema_prop_value.split('/')[-1]}: {ref_value!r} not found within {schema_prop_value!r}"
    )


class _Validator(jsonschema.Draft7Validator):
    """
    This _Validator will additionally check intra-doc refs.
    So say we have this schema:
        {
            "properties": {
                "objs": {
                    "type:": "array",
                    "items": {"type": "object", "required": ["id"]},
                },
                "refs": {
                    "type:": "array",
                    "items": {"in_doc_ref_pattern": "/objs/*/id"},
                },
            }
        }

    This Validator will allow for these docs:
        {
            "objs": [{"id":1}, {"id":"something"}],
            "refs": [1, "something"]
        }

        {
            "objs": [{"id":1}, {"id":"something"}],
            "refs": [1]
        }

    but those will be invalid:
        {
            "objs": [{"id":1}, {"id":"something"}],
            "refs": [2, "something", "else"]
        }

        {
            "objs": [],
            "refs": ["anything"]
        }


    It achieves that by first checking everything with regular Draft7Validator,
    and then collecting all refs and checking existence of a corresponding value.

    """

    with open(METASCHEMA_PATH) as metaschema_file:
        META_SCHEMA = json.load(metaschema_file)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._in_doc_refs_cache = None
        self._ignore_in_doc_refs = False

        # TODO consider adding json pointer check to metaschema for in_doc_ref_pattern values
        self.in_doc_ref_validator = jsonschema.validators.create(
            self.META_SCHEMA, validators={"in_doc_ref_pattern": _in_doc_refs_check}
        )(*args, **kwargs)

    @contextmanager
    def _validation_context(self, instance: JSON, ignore_in_doc_refs: bool = False):
        """
        A context manager for building up and tearing down configuration for
        a running our custom validator on a given instance.
        """
        self._ignore_in_doc_refs = ignore_in_doc_refs
        self._in_doc_refs_cache = dict()

        # Build the in_doc_refs_cache if we're not ignoring in_doc_refs
        if not ignore_in_doc_refs:
            search = DeepSearch(self.schema, "in_doc_ref_pattern")
            if "matched_paths" in search:
                for path in search["matched_paths"]:
                    scope = {"root": self.schema}
                    exec(f"ref_path_pattern = {path}", scope)
                    ref_path_pattern = scope["ref_path_pattern"]
                    # If there are no cached values for this ref path pattern, collect them
                    if ref_path_pattern not in self._in_doc_refs_cache:
                        self._in_doc_refs_cache[
                            ref_path_pattern
                        ] = self._get_values_for_path_pattern(
                            ref_path_pattern, instance
                        )

        # see: https://docs.python.org/3/library/contextlib.html
        try:
            yield
        finally:
            self._in_doc_refs_cache = None

    def validate(
        self, instance: JSON, *args, ignore_in_doc_refs: bool = False, **kwargs
    ):
        with self._validation_context(instance, ignore_in_doc_refs):
            super().validate(instance, *args, **kwargs)

    def iter_errors(self, instance: JSON, _schema: Optional[dict] = None):
        """
        NOTE: do not call this directly! Doing so will break the in_doc_refs validation!

        This is the main validation method. `.is_valid`, `.validate` are based on this.

        It will be called recursively, while `.descend`ing instance and schema.
        """
        # First we call usual Draft7Validator validation
        for downstream_error in super().iter_errors(instance, _schema):
            # and if an error is not "ours" - just propagate it up
            if not isinstance(downstream_error, InDocRefNotFoundError):
                yield downstream_error
            # if it is "ours" - we actually check ref
            elif (
                repr(downstream_error.instance)
                not in self._in_doc_refs_cache[downstream_error.validator_value]
            ):
                # and if the check was not passed - we propagate it
                yield downstream_error

        # Don't perform referential integrity checks if _ignore_in_doc_refs = True
        if self._ignore_in_doc_refs:
            return

        # Here we actually call our custom validator, that will throw errors
        # on every occurrence of `in_doc_ref_pattern` constraint
        for in_doc_ref_not_found in self.in_doc_ref_validator.iter_errors(
            instance, _schema
        ):
            # If the in_doc_refs cache is None at this point in the code,
            # we know that it wasn't initialized properly - this generally means
            # some client code called `self.iter_errors` directly, which
            # isn't allowed.
            if self._in_doc_refs_cache is None:
                raise AssertionError(
                    "_Validator.iter_errors cannot be called directly. Please call _Validator.safe_iter_errors instead."
                )

            # but then we actually check refs
            if (
                repr(in_doc_ref_not_found.instance)
                not in self._in_doc_refs_cache[in_doc_ref_not_found.validator_value]
            ):
                # and produce errors only when check wont pass
                yield in_doc_ref_not_found

    def safe_iter_errors(
        self,
        instance: JSON,
        _schema: Optional[dict] = None,
        ignore_in_doc_refs: bool = False,
    ):
        """A generator producing validation errors for the given JSON instance."""
        with self._validation_context(instance, ignore_in_doc_refs):
            for error in self.iter_errors(instance, _schema):
                yield error
            # restore to default value
            self._ignore_in_doc_refs = False

    def iter_error_messages(self, instance: JSON, _schema: Optional[dict] = None):
        """
        A wrapper for `_Validator.iter_errors` that generates friendlier, shorter error
        messages representing `ValidationError`s.
        """
        for error in self.safe_iter_errors(instance, _schema):
            yield format_validation_error(error)

    def _get_values_for_path_pattern(self, path: str, doc: dict) -> set:
        """
        Search `doc` for every value matching `path`, and return those values as a set.

        Path can contain wildcards (e.g., `/my/path/*/with/wildcard/*/hooray`) but partial
        matching on path subparts is NOT supported (e.g., `/my/part*/path`).
        """
        split_path = path.strip("/").split("/")

        values = [doc]
        for key in split_path:
            next_values = []
            for doc in values:
                if key == "*":
                    # Wild card encountered, so we'll want to search
                    # all values of `doc` if `doc` is a list or a dict
                    if isinstance(doc, list):
                        next_values.extend(doc)
                    elif isinstance(doc, dict):
                        next_values.extend(doc.values())
                elif key in doc:
                    # Non-wild card key, so we'll only want to search
                    # the value in `doc` with key `key`
                    next_values.append(doc[key])
                else:
                    # Handle possibility that `key` is an integer
                    try:
                        index = int(key)
                        next_values.append(doc[index])
                    except ValueError:
                        pass
            values = next_values

        return set(repr(val) for val in values)


def _map_refs(node: dict, on_refs: Callable[[str], dict]) -> dict:
    """
    Apply `on_refs` to all nodes with `$ref`, returning node with refs replaced
    with results of the function call.

    Note: _map_refs is shallow, i.e., if calling `on_refs` on a node produces
    a new node that contains refs, those refs will not be resolved.
    """
    if isinstance(node, collections.abc.Mapping):
        if "$ref" in node or "type_ref" in node:
            ref_key = "$ref" if "$ref" in node else "type_ref"

            if ref_key == "$ref":
                # # Explicitly allow description on a $ref for public documentation,
                # # reserving $comment for developer documentation.
                extra_keys = set(node.keys()).difference(
                    {"$ref", "$comment", "description"}
                )
                if extra_keys:
                    # As for json-schema.org:
                    # "... You will always use $ref as the only key in an object:
                    # any other keys you put there will be ignored by the validator."
                    # So we raise on that, to notify schema creator that s/he should not
                    # expect those additional keys to be verified by schema validator.
                    raise Exception(
                        f"Schema node with '$ref' should not contain anything else besides 'description' for public docs (or '$comment' for dev docs). \
                        \nOn: {node} \nOffending keys {extra_keys}"
                    )

            # We found a ref, so return it mapped through `on_refs`
            new_node = on_refs(node[ref_key])

            if ref_key == "type_ref":
                # For type_ref's, we don't want to clobber the other properties in node,
                # so merge new_node and node.
                new_node.update(node)

            # Keep old 'description' field from next to $ref;
            # this is for user-facing documentation.
            if "description" in node and node["description"]:
                new_node["description"] = node["description"]

            # Plus concatenate new and old '$comment' fields;
            # this is for dev-side documentation side and
            # shouldn't be shown to users.
            if "$comment" in new_node or "$comment" in node:
                new_node["$comment"] = new_node.get("$comment", "") + node.get(
                    "$comment", ""
                )
            return new_node
        else:
            # Look for all refs further down in this mapping
            for k, v in node.items():
                node[k] = _map_refs(v, on_refs)
    elif isinstance(node, (list, tuple)):
        # Look for all refs in this list
        for i in range(len(node)):
            node[i] = _map_refs(node[i], on_refs)
    return node


def _build_ref_resolver(
    schema_root: str, schema_instance: dict
) -> jsonschema.RefResolver:
    base_uri = f"file://{schema_root}/"
    return jsonschema.RefResolver(base_uri, schema_instance)


def _resolve_refs(schema_root: str, json_spec: dict, context: str) -> dict:
    """
    Resolve JSON Schema references in `json_spec` relative to `base_uri`,
    return `json_spec` with all references inlined. `context` is used to
    format error to provide (wait for it) context.
    """
    resolver = _build_ref_resolver(schema_root, json_spec)

    def _resolve_ref(ref: str) -> dict:
        # Don't resolve local refs, since this would make loading recursive schemas impossible.
        if ref.startswith("#"):
            return {"$ref": ref}

        with resolver.resolving(ref) as resolved_spec:
            # resolved_spec might have unresolved refs in it, so we pass
            # it back to _resolve_refs to resolve them. This way,
            # we can fully resolve schemas with nested refs.

            try:
                res = _resolve_refs(schema_root, resolved_spec, ref)
            except RefResolutionError as e:
                raise RefResolutionError(f"Error resolving '$ref':{ref!r}: {e}") from e

            # as reslover uses cache we don't want to return mutable
            # objects, so we make a copy
            return copy.deepcopy(res)

    try:
        return _map_refs(json_spec, _resolve_ref)
    except RefResolutionError as e:
        raise RefResolutionError(f"Error resolving refs in {context!r}: {e}") from e


def _load_dont_validate_schema(
    schema_path: str,
    schema_root: str = SCHEMA_DIR,
    on_refs: Optional[Callable[[dict], dict]] = None,
) -> Union[dict, jsonschema.Draft7Validator]:
    """
    Try to load a valid schema at `schema_path`. The provided `schema_path` can include a
    subschema pointer to load only the subschema at the provided path. For example,
    `my/schema/path.json#properties/subschema` would load only the schema tree below the
    `subschema` property.

    If an `on_refs` function is supplied, call that on all refs in the schema, rather than
    resolving the refs. Note: it is shallow, i.e., if calling `on_refs` on a node produces
    a new node that contains refs, those refs will not be resolved.

    If return validator is true it will return
    the validator and the schema used in the validator.
    """

    assert os.path.isabs(schema_root), "schema_root must be an absolute path"

    # Check if the schema path includes a subschema pointer, e.g.
    #   "my/schema.json#properties/my_property"
    # where "my/schema.json" is the path and "properties/my_property"
    # is the subschema pointer.
    subschema_pointer = None
    if "#" in schema_path:
        schema_path, subschema_pointer = schema_path.split("#", 1)
        if not subschema_pointer.startswith("/"):
            subschema_pointer = f"/{subschema_pointer}"

    # Load schema with resolved $refs
    schema_path = os.path.join(schema_root, schema_path)
    with open(schema_path) as schema_file:
        try:
            json_spec = json.load(schema_file)
        except Exception as e:
            raise Exception(f"Failed loading json {schema_file}") from e

        # If there's a subschema pointer, resolve it and only
        # load the subpart of the JSON schema
        if subschema_pointer:
            json_spec = resolve_pointer(json_spec, subschema_pointer)
        if on_refs:
            schema = _map_refs(json_spec, on_refs)
        else:
            schema = _resolve_refs(schema_root, json_spec, schema_path)

    return schema


_validator_instance = _Validator({})


@functools.lru_cache(maxsize=32)
def load_and_validate_schema(
    schema_path: str,
    schema_root: str = SCHEMA_DIR,
    return_validator: bool = False,
    on_refs: Optional[Callable[[dict], dict]] = None,
) -> Union[dict, jsonschema.Draft7Validator]:
    schema = _load_dont_validate_schema(schema_path, schema_root, on_refs)

    # Ensure schema is valid
    # NOTE: $refs were resolved above, so no need for a RefResolver here
    _validator_instance.check_schema(schema)

    if not return_validator:
        return schema
    else:
        validator = _Validator(schema)
        validator.resolver = _build_ref_resolver(schema_root, schema)
        return validator


# Warm up the cache with a full clinical trial validator
load_and_validate_schema("clinical_trial.json", return_validator=True)


def validate_instance(instance: str, schema: dict, is_required=False) -> Optional[str]:
    """
    Validate a data instance against a JSON schema.

    Returns None if `instance` is valid, otherwise returns reason for invalidity.
    """
    try:
        if instance is None:
            if is_required:
                raise jsonschema.ValidationError("found empty value for required field")
            else:
                return None

        stype = schema.get("format")
        if not stype:
            stype = schema.get("type")
        if not stype:
            if "allOf" in schema:
                types = set(s.get("type") for s in schema["allOf"] if "type" in s)
                # if all types in 'allOf' are the same:
                if len(types) == 1:
                    stype = types.pop()
                else:
                    return (
                        f"Value can't be of multiple different types ({types}), "
                        "as 'allOf' in schema specifies."
                    )

        instance = convert(stype, instance)

        jsonschema.validate(
            # we're using this to validate only 'basic' values that come from Template cells
            # that's why we don't want to check for ref integrity with _Validator here
            # so a Validator specified in this schema will be used, or a default one
            instance,
            schema,
            format_checker=jsonschema.FormatChecker(),
        )
        return None
    except jsonschema.ValidationError as error:
        return error.message


# Methods for reformatting strings


def _get_datetime(value):
    return dateparser.parse(str(value))


def _to_date(value):
    dt = _get_datetime(value)
    if not dt:
        raise ValueError(f'could not convert "{value}" to date')
    return dt.strftime("%Y-%m-%d")


def _to_time(value):
    dt = _get_datetime(value)
    if not dt:
        raise ValueError(f'could not convert "{value}" to time')
    return dt.strftime("%H:%M:%S")


def _to_datetime(value):
    dt = _get_datetime(value)
    if not dt:
        raise ValueError(f'could not convert "{value}" to datetime')
    return dt.isoformat()


def _to_bool(value):
    if isinstance(value, (bool)):
        return value
    else:
        raise ValueError(f'could not convert "{value}" to boolean')


def convert(fmt: str, value: str) -> str:
    """Try to convert a value to the given format"""
    if fmt == "time":
        reformatter = _to_time
    elif fmt == "date":
        reformatter = _to_date
    elif fmt == "string":
        reformatter = lambda n: n and str(n)
    elif fmt == "integer":
        reformatter = lambda n: n and int(n)
    elif fmt == "boolean":
        reformatter = _to_bool
    elif fmt == "number":
        reformatter = lambda n: n and float(n)
    else:
        # If we don't have a specified reformatter, use the identity function
        reformatter = id

    try:
        return reformatter(value)
    except Exception as e:
        raise jsonschema.ValidationError(e)


REQUIRED_PROPERTY_MSG = " is a required property"


def format_validation_error(e: ValidationError) -> str:
    """Produce a short(er), human-friendly(er) jsonschema.ValidationError message."""

    def build_message(field: str):
        message = e.message
        if REQUIRED_PROPERTY_MSG in e.message:
            prop_name = e.message.split(REQUIRED_PROPERTY_MSG)[0]
            message = f"missing required property {prop_name}"

        return f"error on {field}={e.instance}: {message}"

    depth = len(e.absolute_path)

    if depth == 0:
        return build_message("[root]")
    if depth == 1:
        return build_message(e.absolute_path[0])

    # Handle potentially nested array fields, going up in depth until
    # a named property is found
    field = ""
    for path_part in list(e.absolute_path)[::-1]:
        if isinstance(path_part, int):
            field = f"[{path_part}]{field}"
        else:
            field = f"{path_part}{field}"
            break

    return build_message(field)
