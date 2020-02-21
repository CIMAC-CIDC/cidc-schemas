#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for data model schemas."""

import os
import unittest
import pytest
import json
import jsonschema

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
    """Ensure the schema file conforms to JSON schema draft 7"""
    assert load_and_validate_schema(schema_path)
