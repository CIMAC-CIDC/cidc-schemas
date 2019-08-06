#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for artifact schemas"""

import os
import json

import pytest

import jsonschema
from cidc_schemas.json_validation import load_and_validate_schema
from .constants import SCHEMA_DIR

BASE_OBJ = {
    "artifact_category": "Manifest File",
    "artifact_creator": "DFCI",
    "assay_category": "Whole Exome Sequencing (WES)",
    "object_url": "dummy",
    "file_name": "dummy.txt",
    "file_size_bytes": 1,
    "file_type": "FASTA",
    "md5_hash": "dummy",
    "uploaded_timestamp": "dummy",
    "uploader": "dummy",
    "uuid": "dummy",
    "visible": True
}


def _fetch_validator(name):

    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "artifacts/artifact_%s.json" % name)
    schema = load_and_validate_schema(schema_path, schema_root)

    # create validator assert schemas are valid.
    return jsonschema.Draft7Validator(schema)


def test_text():

    # create validator assert schemas are valid.
    obj = BASE_OBJ.copy()
    at_validator = _fetch_validator("text")
    at_validator.validate(obj)

    # assert we can fail it.
    del obj['md5_hash']
    with pytest.raises(jsonschema.ValidationError):
        at_validator.validate(obj)


def test_image():

    # create validator assert schemas are valid.
    at_validator = _fetch_validator("image")

    # create a dummy info
    obj = BASE_OBJ.copy()
    obj['height'] = 128
    obj['width'] = 128
    obj['channels'] = 8
    at_validator.validate(obj)


def test_binary():

    # create validator assert schemas are valid.
    at_validator = _fetch_validator("binary")

    # create a dummy info
    obj = BASE_OBJ.copy()
    obj['info'] = {"test": 128}
    at_validator.validate(obj)


def test_csv():

    # create validator assert schemas are valid.
    at_validator = _fetch_validator("csv")

    # create a dummy info
    obj = BASE_OBJ.copy()
    obj["header_row"] = 128
    obj["seperator"] = ","
    at_validator.validate(obj)
