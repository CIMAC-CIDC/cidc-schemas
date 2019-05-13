# -*- encoding: utf-8 -*-

"""Tools for performing validations based on json schemas"""

from typing import Optional

import dateparser
import jsonschema


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
        reformatter = str
    else:
        # If we don't have a specified reformatter, use the identity function
        reformatter = id

    try:
        return reformatter(value)
    except Exception as e:
        raise jsonschema.ValidationError(e)
