# -*- encoding: utf-8 -*-

"""Tools for performing validations based on json schemas"""

import os
import json
import collections
from typing import Optional

import dateparser
import jsonschema

SCHEMA_ROOT = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'schemas')


def load_and_validate_schema(schema_path: str, schema_root: str = SCHEMA_ROOT) -> dict:
    """
    Try to load a valid schema at `schema_path`.
    """
    assert os.path.isabs(
        schema_root), "schema_root must be an absolute path"

    # Load schema with resolved $refs
    with open(schema_path) as schema_file:
        base_uri = f'file://{schema_root}/'
        json_spec = json.load(schema_file)
        schema = _resolve_refs(base_uri, json_spec)

    # Ensure schema is valid
    # NOTE: $refs were resolved above, so no need for a RefResolver here
    validator = jsonschema.Draft7Validator(schema)
    validator.check_schema(schema)

    return schema


def _resolve_refs(base_uri: str, json_spec: dict):
    """
    Resolve JSON references in `json_spec` relative to `base_uri`,
    return `json_spec` with all references inlined.
    """
    resolver = jsonschema.RefResolver(base_uri, json_spec)

    def _do_resolve(node):
        if '$ref' in node:
            # We found a ref, so return it
            with resolver.resolving(node['$ref']) as resolved:
                return resolved
        elif isinstance(node, collections.Mapping):
            # Look for all refs in this mapping
            for k, v in node.items():
                node[k] = _do_resolve(v)
        elif isinstance(node, (list, tuple)):
            # Look for all refs in this list
            for i in range(len(node)):
                node[i] = _do_resolve(node[i])
        return node

    return _do_resolve(json_spec)


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
    else:
        # If we don't have a specified reformatter, use the identity function
        reformatter = id

    try:
        return reformatter(value)
    except Exception as e:
        raise jsonschema.ValidationError(e)
