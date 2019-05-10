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
        # Check if value needs formatting
        if 'format' in schema:
            instance = coerce(schema['format'], instance)

        jsonschema.validate(
            instance, schema, format_checker=jsonschema.FormatChecker())
        return None
    except jsonschema.ValidationError as error:
        return error.message


# Methods for reformatting strings

def _get_datetime(value):
    # get datetime
    dt = dateparser.parse(str(value))

    if not dt:
        raise ValueError(f"Could not convert {value} to datetime")

    return dt


def _to_date(value):
    return _get_datetime(value).strftime('%Y-%m-%d')


def _to_time(value):
    return _get_datetime(value).strftime('%H:%M:%S')


def coerce(fmt: str, value: str) -> str:
    """Try to coerce a value to its specified format"""
    if fmt == 'time':
        coercer = _to_time
    elif fmt == 'date':
        coercer = _to_date
    else:
        # If we don't have a specified coercer, use the identity function
        coercer = id

    try:
        return coercer(value)
    except Exception as e:
        raise jsonschema.ValidationError(e)
