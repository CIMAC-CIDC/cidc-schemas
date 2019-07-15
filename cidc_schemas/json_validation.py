# -*- encoding: utf-8 -*-

"""Tools for performing validations based on json schemas"""

import os
import json
import collections
from typing import Optional, List, Callable, Union

import dateparser
import jsonschema

from .constants import SCHEMA_DIR


def load_and_validate_schema(
        schema_path: str,
        schema_root: str = SCHEMA_DIR,
        return_validator: bool = False,
        on_refs: Optional[Callable] = None) -> Union[dict, jsonschema.Draft7Validator]:
    """
    Try to load a valid schema at `schema_path`. If an `on_refs` function
    is supplied, call that on all refs in the schema, rather than
    resolving the refs. If return validator is true it will return
    the validator and the schema used in the validator.
    validator.
    """
    assert os.path.isabs(
        schema_root), "schema_root must be an absolute path"

    # Load schema with resolved $refs
    schema_path = os.path.join(schema_root, schema_path)
    with open(schema_path) as schema_file:
        base_uri = f'file://{schema_root}/'
        json_spec = json.load(schema_file)
        if on_refs:
            schema = _map_refs(json_spec, on_refs)
        else:
            schema = _resolve_refs(base_uri, json_spec)

    # Ensure schema is valid
    # NOTE: $refs were resolved above, so no need for a RefResolver here
    validator = jsonschema.Draft7Validator(schema)
    validator.check_schema(schema)

    if not return_validator:
        return schema
    else:
        return validator


def _map_refs(node: dict, fn: Callable):
    """
    Apply `fn` to all refs in node, returning node with refs replaced
    with results of the function call.

    Note: _map_refs is shallow, i.e., if calling `fn` on a node produces 
    a new node that contains refs, those refs will not be resolved.
    """
    if isinstance(node, collections.Mapping) and '$ref' in node:
        # We found a ref, so return it
        return fn(node['$ref'])
    elif isinstance(node, collections.Mapping):
        # Look for all refs in this mapping
        for k, v in node.items():
            node[k] = _map_refs(v, fn)
    elif isinstance(node, (list, tuple)):
        # Look for all refs in this list
        for i in range(len(node)):
            node[i] = _map_refs(node[i], fn)
    return node


def _resolve_refs(base_uri: str, json_spec: dict) -> dict:
    """
    Resolve JSON Schema references in `json_spec` relative to `base_uri`,
    return `json_spec` with all references inlined.
    """
    resolver = jsonschema.RefResolver(base_uri, json_spec)

    def _resolve_ref(ref):
        with resolver.resolving(ref) as resolved_spec:
            # resolved_spec might have unresolved refs in it, so we pass
            # it back to _resolve_refs to resolve them. This way,
            # we can fully resolve schemas with nested refs.
            return _resolve_refs(base_uri, resolved_spec)

    return _map_refs(json_spec, _resolve_ref)


def validate_instance(instance: str, schema: dict, required: bool) -> Optional[str]:
    """
    Validate a data instance against a JSON schema.

    Returns None if `instance` is valid, otherwise returns reason for invalidity.
    """
    try:
        if not instance:
            if required:
                raise jsonschema.ValidationError(
                    'found empty value for required field')
            else:
                return None

        instance = convert(schema.get('format') or schema['type'], instance)

        jsonschema.validate(
            instance, schema, format_checker=jsonschema.FormatChecker())
        return None
    except jsonschema.ValidationError as error:
        return error.message


# Methods for reformatting strings

def _get_datetime(value):
    return dateparser.parse(str(value))


def _to_date(value):
    dt = _get_datetime(value)
    if not dt:
        raise ValueError(f"could not convert \"{value}\" to date")
    return dt.strftime('%Y-%m-%d')


def _to_time(value):
    dt = _get_datetime(value)
    if not dt:
        raise ValueError(f"could not convert \"{value}\" to time")
    return dt.strftime('%H:%M:%S')


def _to_bool(value):
    if isinstance(value, (bool)):
        return value
    else:
        raise ValueError(f"could not convert \"{value}\" to boolean")


def convert(fmt: str, value: str) -> str:
    """Try to convert a value to the given format"""
    if fmt == 'time':
        reformatter = _to_time
    elif fmt == 'date':
        reformatter = _to_date
    elif fmt == 'string':
        def reformatter(n): return n and str(n)
    elif fmt == 'integer':
        def reformatter(n): return n and int(n)
    elif fmt == 'boolean':
        reformatter = _to_bool
    else:
        # If we don't have a specified reformatter, use the identity function
        reformatter = id

    try:
        return reformatter(value)
    except Exception as e:
        raise jsonschema.ValidationError(e)
