#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for data model schemas."""

import os
import pytest

from cidc_schemas.json_validation import load_and_validate_schema
from .constants import SCHEMA_DIR


def schema_paths():
    """Get the path to every schema in the schemas directory"""
    schema_paths = []
    for root, _, files in os.walk(SCHEMA_DIR):
        files = [f for f in files if not f[0] == "."]
        for f in files:

            # skipping templates
            if f.endswith("_template.json"):
                continue

            schema_paths.append(os.path.join(root, f))

    return schema_paths


@pytest.mark.parametrize("schema_path", schema_paths(), ids=lambda x: x.split("/")[-1])
def test_schema(schema_path):
    """Ensure the schema file conforms to JSON schema draft 2020-12"""
    assert load_and_validate_schema(schema_path)


def recursive_additionalProperties(schema: dict, name: str):
    if not isinstance(schema, dict):
        return

    if schema.get("type") == "object":
        assert "additionalProperties" in schema or schema.get("inheritableBase"), name

    for k, v in schema.items():
        recursive_additionalProperties(v, name + "/" + k)


def test_additionalProperties():
    ct_schema = load_and_validate_schema(
        os.path.join(SCHEMA_DIR, "clinical_trial.json")
    )
    recursive_additionalProperties(ct_schema, "")
