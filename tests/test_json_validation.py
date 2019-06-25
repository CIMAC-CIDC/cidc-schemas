#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for JSON loading/validation utilities."""

import os
import json

import pytest

from cidc_schemas.json_validation import _map_refs, _resolve_refs
from .constants import TEST_SCHEMA_DIR


def test_map_refs():
    spec = {"a": {"$ref": "foo"}, "b": [{"$ref": "foo"}]}

    target = {"a": "FOO", "b": ["FOO"]}

    assert _map_refs(spec, lambda ref: ref.upper()) == target


def do_resolve(schema_path):
    base_uri = f"file://{TEST_SCHEMA_DIR}/"

    with open(os.path.join(TEST_SCHEMA_DIR, schema_path)) as f:
        spec = json.load(f)
        return _resolve_refs(base_uri, spec)


def test_resolve_refs():
    """Ensure that ref resolution can handle nested refs"""

    # One level of nesting
    b = do_resolve("b.json")
    assert b["properties"] == {"b_prop": {"c_prop": {"type": "string"}}}

    # Two levels of nesting
    a = do_resolve("a.json")
    assert a["properties"] == {"a_prop": b["properties"]}

    # Two levels of nesting across different directories
    one = do_resolve("1.json")
    assert one["properties"] == {"1_prop": {"2_prop": {"3_prop": {"type": "string"}}}}
