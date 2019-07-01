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

ASSAY_CORE = {
  "assay_creator": "DFCI",
  "uploader": "dummy",
  "assay_category": "Whole Exome Sequencing (WES)"
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
  obj = {**ASSAY_CORE, **ngs_obj}    # merge two dictionaries

  # create the wes object
  fastq_1 = ARTIFACT_OBJ.copy()
  rgmf = ARTIFACT_OBJ.copy()
  rgmf['artifact_category'] = 'Assay Artifact from CIMAC'
  record = {
    "enrichment_vendor_kit": "Twist",
    "enrichment_vendor_lot": "dummy_value", 
    "capture_date": "01/01/2001",
    "files": {
      "tumor": {
        "fastq_1": fastq_1,
        "fastq_2": fastq_1
      },
      "normal": {
        "fastq_1": fastq_1,
        "fastq_2": fastq_1
      },
      "read_group_mapping_file": rgmf
    }
  }

  # add a demo record.
  obj['records'] = [
    record
  ]
  

  # create validator assert schemas are valid.
  validator = _fetch_validator("wes")
  validator.validate(obj)

  # assert negative behaviors
  del obj['records'][0]['enrichment_vendor_kit']
  with pytest.raises(jsonschema.ValidationError):
    validator.validate(obj)


def test_rna_expression():

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
  obj = {**ASSAY_CORE, **ngs_obj}    # merge two dictionaries

  # add custom entry
  obj['enrichment_method'] = "Ribo minus"

  # create the wes object
  fastq_1 = ARTIFACT_OBJ.copy()
  rgmf = ARTIFACT_OBJ.copy()
  rgmf['artifact_category'] = 'Assay Artifact from CIMAC'
  record = {
    "enrichment_vendor_kit": "Twist",
    "enrichment_vendor_lot": "dummy_value", 
    "capture_date": "01/01/2001",
    "files": {
        "fastq_1": fastq_1,
        "fastq_2": fastq_1,
        "read_group_mapping_file": rgmf
      }
  }
  

  # add a demo record.
  obj['records'] = [
    record
  ]
  

  # create validator assert schemas are valid.
  validator = _fetch_validator("rna_expression")
  validator.validate(obj)

  # assert negative behaviors
  del obj['records'][0]['enrichment_vendor_kit']
  with pytest.raises(jsonschema.ValidationError):
    validator.validate(obj)
