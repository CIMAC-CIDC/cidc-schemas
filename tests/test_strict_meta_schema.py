#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for strict meta schema."""

import os
import unittest
import pytest
import json
import jsonschema

from cidc_schemas.json_validation import _validator_instance


def check_valid(schema: dict):
    _validator_instance.check_schema(schema)
    assert True


def check_raises(schema: dict, match: str = ""):
    with pytest.raises(jsonschema.exceptions.SchemaError, match=match):
        _validator_instance.check_schema(schema)


def test_valid_simple_schema():
    check_valid({"type": "string"})


def test_valid_custom_prism_keywords_schema():
    check_valid({"type": "string", "in_doc_ref_pattern": "whatever"})


def test_valid_base_schema():
    check_valid(
        {
            "$schema": "metaschema/strict_meta_schema.json#",
            "$id": "valid_base",
            "type": "object",
            "inheritableBase": True,
            "properties": {
                "first_prop": {"type": "string"},
                "second_prop": {"type": "array"},
            },
        }
    )


def test_valid_simple_schema():
    check_valid(
        {
            "$schema": "metaschema/strict_meta_schema.json#",
            "$id": "valid_simple",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "first_prop": {"type": "string"},
                "second_prop": {"type": "array"},
            },
        }
    )


def test_valid_jsonmerge():
    check_valid(
        {
            "$schema": "metaschema/strict_meta_schema.json#",
            "$id": "valid_jsonmerge",
            "type": "array",
            "mergeStrategy": "something",
            "mergeOptions": "else",
        }
    )


def test_invalid_implicit_object_schema():
    check_raises(
        {
            "$schema": "metaschema/strict_meta_schema.json#",
            "$id": "invalid_implicit_object",
            "properties": {
                "first_prop": {"type": "string"},
                "second_prop": {"type": "array"},
            },
        },
        "is not valid",
    )


def test_invalid_explicit_object_schema():
    check_raises(
        {
            "$schema": "metaschema/strict_meta_schema.json#",
            "$id": "invalid_explicit_object",
            "type": "object",
        },
        "is not valid",
    )


def test_invalid_nested_schema():
    check_raises(
        {
            "$schema": "metaschema/strict_meta_schema.json#",
            "$id": "valid_simple",
            "type": "object",
            "additionalProperties": False,
            "properties": {"first_prop": {"type": "object"}},
        },
        "is not valid",
    )


def test_free_schema():
    check_raises({"$schema": "metaschema/strict_meta_schema.json#"}, "is not valid")


def test_empty_schema():
    check_valid(
        {
            "$schema": "metaschema/strict_meta_schema.json#",
            "additionalProperties": False,
        }
    )
