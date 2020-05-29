# -*- encoding: utf-8 -*-

"""Tools for performing validations based on json schemas"""

import os
import json
import copy
import fnmatch
import collections.abc
import functools
from typing import Optional, List, Callable, Union

import dateparser
import jsonschema
from jsonschema.exceptions import ValidationError, RefResolutionError

from .constants import SCHEMA_DIR, METASCHEMA_PATH
from .util import get_all_paths, split_python_style_path, JSON


class InDocRefNotFoundError(ValidationError):
    pass


def _in_doc_refs_check(validator, schema_prop_value, ref_value, subschema):
    """ A "dummy" validator, that just produces errors for every occurrence of `in_doc_ref_pattern` """
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

        # TODO consider adding json pointer check to metaschema for in_doc_ref_pattern values
        self.in_doc_ref_validator = jsonschema.validators.create(
            self.META_SCHEMA, validators={"in_doc_ref_pattern": _in_doc_refs_check}
        )(*args, **kwargs)

    def iter_errors(self, instance: JSON, _schema: Optional[dict] = None):
        """ 
        This is the main validation method. `.is_valid`, `.validate` are based on this. 
    
        It will be called recursively, while `.descend`ing instance and schema.
        """
        in_doc_refs_cache = {}

        # First we call usual Draft7Validator validation
        for downstream_error in super().iter_errors(instance, _schema):
            # and if an error is not "ours" - just propagate it up
            if not isinstance(downstream_error, InDocRefNotFoundError):
                yield downstream_error
            # if it is "ours" - we actually check ref
            elif not self._ensure_in_doc_ref(
                # error.instance - is value in doc that should satisfy a constraint
                ref=downstream_error.instance,
                # error.validator_value - is value of a constraint from schema,
                # which should be in a form of path pattern, where ref value needs to be present.
                ref_path_pattern=downstream_error.validator_value,
                doc=instance,
                in_doc_refs_cache=in_doc_refs_cache,
            ):
                # and if the check was not passed - we propagate it
                yield downstream_error

        # Here we actually call our custom validator, that will through errors
        # on every occurrence of `in_doc_ref_pattern` constraint
        for in_doc_ref_not_found in self.in_doc_ref_validator.iter_errors(
            instance, _schema
        ):
            # but then we actually check refs
            if not self._ensure_in_doc_ref(
                ref=in_doc_ref_not_found.instance,
                ref_path_pattern=in_doc_ref_not_found.validator_value,
                doc=instance,
                in_doc_refs_cache=in_doc_refs_cache,
            ):
                # and produce errors only when check wont pass
                yield in_doc_ref_not_found

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

    def _ensure_in_doc_ref(
        self, ref: str, ref_path_pattern: str, doc: JSON, in_doc_refs_cache: dict
    ):
        """
        This checks that a `ref` (think foreign key) can be found within a `doc` (JSON object),
        and it's location (json pointer path) should match `ref_path_pattern`. 
        
        ref_path_pattern might be in `fnmatch` form

        E.g.

        >>> doc = {"objs": [{"id":"1"}, {"id":"something"}]}
        >>> _Validator({})._ensure_in_doc_ref("something", "/objs/*/id", doc)
        True

        >>> _Validator({})._ensure_in_doc_ref("1", "/objs/*/id", doc)
        True
        
        >>> _Validator({})._ensure_in_doc_ref("something_else", "/objs/*/id", doc)
        False

        
        >>> _Validator({})._ensure_in_doc_ref("something", "/objs", doc)
        False

        """
        if not (self.is_type(doc, "object") or self.is_type(doc, "array")):
            # if we're in a "simple value" context,
            # we can't possibly match ref_path_pattern
            return False

        # If there are no cached values for this ref path pattern, collect them
        if ref_path_pattern not in in_doc_refs_cache:
            vals = self._get_values_for_path_pattern(ref_path_pattern, doc)
            if len(vals) == 0:
                # There are no values matching this pattern, so there's
                # no way `ref` can match a value with this pattern.
                return False
            else:
                # Cache the collected values for this path
                in_doc_refs_cache[ref_path_pattern] = vals

        # Check if `ref` is among valid values for this pattern
        return repr(ref) in in_doc_refs_cache[ref_path_pattern]


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
                extra_keys = set(node.keys()).difference({"$ref", "$comment"})
                if extra_keys:
                    # As for json-schema.org:
                    # "... You will always use $ref as the only key in an object:
                    # any other keys you put there will be ignored by the validator."
                    # So we raise on that, to notify schema creator that s/he should not
                    # expect those additional keys to be verified by schema validator.
                    raise Exception(
                        f"Schema node with '$ref' should not contain anything else (besides '$comment' for docs). \
                        \nOn: {node} \nOffending keys {extra_keys}"
                    )

            # We found a ref, so return it mapped through `on_refs`
            new_node = on_refs(node[ref_key])

            if ref_key == "type_ref":
                # For type_ref's, we don't want to clobber the other properties in node,
                # so merge new_node and node.
                new_node.update(node)

            # Plus concatenated new and old '$comment' fields
            # which should be just ignored anyways.
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
    Try to load a valid schema at `schema_path`. If an `on_refs` function
    is supplied, call that on all refs in the schema, rather than
    resolving the refs. Note: it is shallow, i.e., if calling `on_refs` on a node produces 
    a new node that contains refs, those refs will not be resolved.

    If return validator is true it will return
    the validator and the schema used in the validator.
    """

    assert os.path.isabs(schema_root), "schema_root must be an absolute path"

    # Load schema with resolved $refs
    schema_path = os.path.join(schema_root, schema_path)
    with open(schema_path) as schema_file:
        try:
            json_spec = json.load(schema_file)
        except Exception as e:
            raise Exception(f"Failed loading json {schema_file}") from e
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
