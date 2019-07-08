#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for JSON loading/validation utilities."""

import os
import json

import pytest
import jsonschema

from cidc_schemas.json_validation import _map_refs, load_and_validate_schema, _resolve_refs
from .constants import SCHEMA_DIR, ROOT_DIR, TEST_SCHEMA_DIR


def test_assay_core():

    # load and validate schema.
    schema_root = SCHEMA_DIR
    micsss_schema_path = os.path.join(SCHEMA_DIR, "assays/micsss_assay.json")

    micsss_schema = load_and_validate_schema(micsss_schema_path, schema_root)

    # create validator assert schemas are valid.
    micsss_validator = jsonschema.Draft7Validator(micsss_schema)
    micsss_validator.check_schema(micsss_schema)

    # create some sample data
    payload = {}
    core_data = {
        "assay_creator": "DFCI"
    }
    payload = {**payload, **core_data}

    # add imaging core data
    image = {
        "protocol_name": "Celebi"
    }
    payload = {**payload, **image}
    antibody = [
        {
            "antibody": "FOXP3",
            "primary_antibody_block": "dummy",
        }
    ]
    payload['payload'] = payload

    # add the data row
    imaging_data = {
        "internal_slide_id": "a1b1"
    }
    payload = {**payload, **imaging_data}

    micsss = {
        "antibody": antibody
    }
    payload = {**payload, **micsss}

    # assert this is valid.
    # micsss_validator.validate(payload)
