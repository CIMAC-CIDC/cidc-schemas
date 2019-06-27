#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for artifact schemas"""

import os
import json

import pytest

import jsonschema
from cidc_schemas.json_validation import load_and_validate_schema
from .constants import SCHEMA_DIR


def test_text():

  # load and validate schema.
  schema_root = SCHEMA_DIR
  at_schema_path = os.path.join(SCHEMA_DIR, "artifacts/artifact_text.json")
  at_schema = load_and_validate_schema(at_schema_path, schema_root)

  print(at_schema.keys())
  print(len(at_schema['allOf']))
  tmp = at_schema['allOf'][0]['properties']
  print(json.dumps(tmp, indent=4, sort_keys=True))
  #for k in tmp:
  #  print(k, tmp[k])

  # example.
  obj = {
    "artifact_category": "Manifest File",
    "artifact_creator": "DFCI",
    "assay_category": "Whole Exome Sequencing (WES)",
    "bucket_url": "dummy",
    "file_name": "dummy.txt",
    "file_size_bytes": 1,
    "file_type": "FASTA",
    "md5_hash": "dummy",
    "uploaded_timestamp": "dummy",
    "uploader": "dummy",
    "uuid": "dummy",
    "visible": True
  }

  # create validator assert schemas are valid.
  at_validator = jsonschema.Draft7Validator(at_schema)

  # create a dummy object.
  at_validator.validate(obj)
