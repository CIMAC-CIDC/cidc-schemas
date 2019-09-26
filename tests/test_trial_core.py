#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests the entire trial core schemas"""

import os
import json

import pytest
import jsonschema

from cidc_schemas.json_validation import _map_refs, load_and_validate_schema, _resolve_refs
from .constants import SCHEMA_DIR, ROOT_DIR, TEST_SCHEMA_DIR

from .test_assays import ASSAY_CORE, ARTIFACT_OBJ, OLINK_RECORD

def _fetch_validator(name):

    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "%s.json" % name)
    schema = load_and_validate_schema(schema_path, schema_root)

    # create validator assert schemas are valid.
    return jsonschema.Draft7Validator(schema)

def _sim_olink():

    # create the olink object
    olink = {**ASSAY_CORE}

    # create the olink object
    text = ARTIFACT_OBJ.copy()
    record = OLINK_RECORD.copy()
    record["files"]["assay_npx"] = text
    record["files"]["assay_raw_ct"] = text
    record["files"]["study_npx"] = text
    olink['records'] = [record]
    
    return olink


def test_aliquot():

    # create basic aliquot
    aliquot = {
        "slide_number": "12",
        "sample_volume_units": "Other",
        "material_used": 1,
        "material_remaining": 0,
        "quality_of_shipment": "Other",
        "aliquot_replacement": "N/A",
        "aliquot_status": "Other"
    }

    # create validator assert schemas are valid.
    validator = _fetch_validator("aliquot")
    validator.validate(aliquot)


def test_clinicaltrial_simple():

    # create the assay
    assays = {
        "olink": _sim_olink()
    }

    # create aliquot
    aliquot = {
        "slide_number": "34",
        "assay": assays,
        "sample_volume_units": "Other",
        "material_used": 1,
        "material_remaining": 0,
        "quality_of_shipment": "Other",
        "aliquot_replacement": "N/A",
        "aliquot_status": "Other"
    }

    # create the sample.
    sample = {
        "cimac_id": "CM-TEST-1234-00",
        "parent_sample_id": "blank",
        "aliquots": [aliquot],
        "collection_event_name": "---",
        "sample_location": "---",
        "type_of_sample": "Other",
        "type_of_primary_container": "Other",
        "genomic_source": "Normal",
    }

    # create the participant
    participant = {
        "cimac_participant_id": "CM-TEST-1234",
        "participant_id": "blank",
        "samples": [sample],
        "cohort_name": "---",
        "arm_id": "---",    
    }

    # create the trial
    ct = {
        "protocol_id": "test",
        "participants": [participant]
    }

    # create validator assert schemas are valid.
    validator = _fetch_validator("clinical_trial")
    validator.validate(ct)


def test_clinicaltrial_olink():

    # create 2 aliquots
    aliquot1 = {
        "slide_number": "13",
        "sample_volume_units": "Other",
        "material_used": 1,
        "material_remaining": 0,
        "quality_of_shipment": "Other",
        "aliquot_replacement": "N/A",
        "aliquot_status": "Other"
    }
    aliquot2 = {
        "slide_number": "14",
        "sample_volume_units": "Other",
        "material_used": 1,
        "material_remaining": 0,
        "quality_of_shipment": "Other",
        "aliquot_replacement": "N/A",
        "aliquot_status": "Other"
    }

    # create the sample.
    sample1 = {
        "cimac_id": "CM-TEST-PA12-34",
        "parent_sample_id": "blank",
        "aliquots": [aliquot1],
        "collection_event_name": "---",
        "sample_location": "---",
        "type_of_sample": "Other",
        "type_of_primary_container": "Other",
        "genomic_source": "Normal",
    }
    sample2 = {
        "cimac_id": "CM-TEST-PAAB-CD",
        "parent_sample_id": "blank",
        "aliquots": [aliquot2],
        "collection_event_name": "---",
        "sample_location": "---",
        "type_of_sample": "Other",
        "type_of_primary_container": "Other",
        "genomic_source": "Normal",
    }

    # create the participant
    participant1 = {
        "cimac_participant_id": "CM-TEST-1234",
        "participant_id": "blank",
        "samples": [sample1],
        "cohort_name": "---",
        "arm_id": "---",    
    }
    participant2 = {
        "cimac_participant_id": "CM-TEST-2222",
        "participant_id": "blank",
        "samples": [sample2],
        "cohort_name": "---",
        "arm_id": "---",    
    }

    # create the trial
    ct = {
        "protocol_id": "test",
        "participants": [participant1, participant2]
    }

    # create validator assert schemas are valid.
    validator = _fetch_validator("clinical_trial")
    validator.validate(ct)