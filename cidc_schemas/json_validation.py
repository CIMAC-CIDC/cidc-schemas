# -*- encoding: utf-8 -*-

"""Tools for performing validations based on json schemas"""

import os
import json
from typing import Optional

import dateparser
import jsonschema
import jsonref

SCHEMA_ROOT = os.path.join(os.path.abspath(__file__), '..', '..', 'schemas')


def load_and_validate_schema(schema_path: str, schema_root: str = SCHEMA_ROOT, titled_refs: bool = False) -> dict:
    """
    Try to load a valid schema at `schema_path`.
    """
    assert os.path.isabs(
        schema_root), "schema_root must be an absolute path"

    loader_kwargs = {
        'base_uri': f'file://{schema_root}/',
        'jsonschema': True
    }

    # Load schema with resolved $refs
    with open(schema_path) as schema_file:
        schema = jsonref.load(schema_file, **loader_kwargs)

    # Ensure schema is valid
    # NOTE: $refs were resolved above, so no need for a RefResolver here
    validator = jsonschema.Draft7Validator(schema)
    validator.check_schema(schema)

    return schema


def validate_instance(instance: str, schema: dict) -> Optional[str]:
    """
    Validate a data instance against a JSON schema.

    Returns None if `instance` is valid, otherwise returns reason for invalidity.
    """
    try:
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
