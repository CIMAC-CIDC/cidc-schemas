#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for artifact schemas"""

import os
import json

import pytest

import jsonschema
from cidc_schemas.json_validation import load_and_validate_schema
from .constants import SCHEMA_DIR

ARTIFACT_OBJ = {
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

def _fetch_validator(name):

  schema_root = SCHEMA_DIR
  schema_path = os.path.join(SCHEMA_DIR, "assays/%s_assay.json" % name)
  schema = load_and_validate_schema(schema_path, schema_root)

  # create validator assert schemas are valid.
  return jsonschema.Draft7Validator(schema)

def test_wes():

  # create the ngs object
  ngs_obj = {
    "sequencer_platform": "Illumina - NovaSeq 6000",
    "library_vendor_kit": "KAPA - Hyper Prep",
    "library_kit_lot": "dummy_value",
    "library_prep_date": "01/01/2001",
    "paired_end_reads": "Paired",
    "read_length": 200,
    "input_ng": 666,
    "library_yield_ng": 666,
    "average_insert_size": 200
  }

  # create the wes object
  wes_obj = {
    "enrichment_vendor_kit": "Twist",
    "enrichment_vendor_lot": "dummy_value", 
    "capture_date": "01/01/2001"
  }
  obj = {**ngs_obj, **wes_obj}    # merge two dictionaries

  # create validator assert schemas are valid.
  validator = _fetch_validator("wes")
  validator.validate(obj)

  # assert negative behaviors
  del obj['enrichment_vendor_kit']
  with pytest.raises(jsonschema.ValidationError):
    validator.validate(obj)


