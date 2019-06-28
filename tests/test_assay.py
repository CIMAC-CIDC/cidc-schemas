#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for JSON loading/validation utilities."""

import os
import json

import pytest
import jsonschema

from cidc_schemas.json_validation import _map_refs, load_and_validate_schema, _resolve_refs
from .constants import SCHEMA_DIR, ROOT_DIR, TEST_SCHEMA_DIR


def test_map_refs():
    spec = {"a": {"$ref": "foo"}, "b": [{"$ref": "foo"}]}

    target = {"a": "FOO", "b": ["FOO"]}

    assert _map_refs(spec, lambda ref: ref.upper()) == target


def test_assay_core():

    # load and validate schema.
    schema_root = SCHEMA_DIR
    micsss_schema_path = os.path.join(SCHEMA_DIR, "assays/micsss_assay.json")

    micsss_schema = load_and_validate_schema(micsss_schema_path, schema_root)

    # create validator assert schemas are valid.
    micsss_validator = jsonschema.Draft7Validator(micsss_schema)
    micsss_validator.check_schema(micsss_schema)

    # create some sample data
    core_data = {"assay_creator": "DFCI"}

    image = {
        "protocol_name": "Celebi"
    }

    antibody = {
        "antibody": "FOXP3",
    }

    micsss_antibody = {
        "primary_antibody_block": "N/A",
    }

    imaging_data = {
        "internal_slide_id": "a1b1"
    }
    # validate the positive version works.
    micsss = {"project_qupath_folder": "n/a",
              "micsss_exported_data_folder": "n/a",
              "core_data": [core_data],
              "images": [image],
              "imaging_data": [imaging_data],
              "antibodies": [antibody],
              "micsss_antibodies": [micsss_antibody]
              }

    micsss_validator.validate(micsss)

    # make it fail
    # micsss.pop('project_qupath_folder')
    # with pytest.raises(jsonschema.ValidationError):
    # micsss_validator.validate(micsss)


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
    assert one["properties"] == {"1_prop": {
        "2_prop": {"3_prop": {"type": "string"}}}}
