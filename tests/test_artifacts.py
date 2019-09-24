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
    "object_url": "dummy",
    "file_name": "dummy.txt",
    "file_size_bytes": 1,
    "data_format": "FASTA",
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


def test_upload_placeholder_oneOf_required():
    """
    Tests whether json schema allows to use something like
        "oneOf": [
          {
            "required": [
              "file_name",
              "object_url",
              "uploaded_timestamp",
              "file_size_bytes",
              "md5_hash",
              "artifact_category"
            ]
          },
          {
            "required": [
              "upload_placeholder"
            ]
          }
        ]
    """

    # create validator assert schemas are valid.
    obj = BASE_OBJ.copy()
    obj['data_format'] = 'CSV'
    at_validator = _fetch_validator("core")
    at_validator.validate(obj)

    # assert we can fail it.
    del obj["file_name"]
    del obj["object_url"]
    del obj["uploaded_timestamp"]
    del obj["file_size_bytes"]
    del obj["md5_hash"]
    del obj["artifact_category"]
    with pytest.raises(jsonschema.ValidationError):
        at_validator.validate(obj)

    obj['upload_placeholder'] = "some uuid or job_id"
    at_validator.validate(obj)

    del obj["upload_placeholder"]
    with pytest.raises(jsonschema.ValidationError):
        at_validator.validate(obj)


def test_text():

    # create validator assert schemas are valid.
    obj = BASE_OBJ.copy()
    obj['data_format'] = 'TEXT'
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
    obj['data_format'] = 'IMAGE'
    obj['height'] = 128
    obj['width'] = 128
    obj['channels'] = 8
    at_validator.validate(obj)


def test_binary():

    # create validator assert schemas are valid.
    at_validator = _fetch_validator("binary")

    # create a dummy info
    obj = BASE_OBJ.copy()
    obj['data_format'] = 'BINARY'
    obj['info'] = {"test": 128}
    at_validator.validate(obj)


def test_csv():

    # create validator assert schemas are valid.
    at_validator = _fetch_validator("csv")

    # create a dummy info
    obj = BASE_OBJ.copy()
    obj['data_format'] = 'CSV'
    obj["header_row"] = 128
    obj["separator"] = ","
    at_validator.validate(obj)


def test_npx():

    # create validator assert schemas are valid.
    at_validator = _fetch_validator("npx")

    # create a dummy info
    obj = BASE_OBJ.copy()
    obj['data_format'] = 'NPX'

    # should fail
    with pytest.raises(jsonschema.ValidationError):
        at_validator.validate(obj)

    # add the required properties
    obj["number_of_samples"] = 7
    obj["samples"] = ["CM-NONE-REFE-RE", "CM-NTIA-INTE-GR"]
    at_validator.validate(obj)
