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
        "cimac_aliquot_id": "1234"
    }

    # create validator assert schemas are valid.
    validator = _fetch_validator("aliquot")
    validator.validate(aliquot)

    # now add a olink but make it invalid
    assays = {
        "olink": {"thisshould": "fail"}
    }
    aliquot['assay'] = assays
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(aliquot) 

    # update olink to be valid
    olink = _sim_olink()
    assays["olink"] = olink

    # assert we can validate this.
    validator.validate(aliquot)

    # try to make an invalid assay
    assays["wes"] = olink.copy()
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(aliquot) 


def test_clinicaltrial_simple():

    # create the assay
    assays = {
        "olink": _sim_olink()
    }

    # create aliquot
    aliquot = {
        "cimac_aliquot_id": "1234",
        "assay": assays
    }

    # create the sample.
    sample = {
        "cimac_sample_id": "S1234",
        "site_sample_id": "blank",
        "aliquots": [aliquot]
    }

    # create the participant
    participant = {
        "cimac_participant_id": "P1234",
        "trial_participant_id": "blank",
        "samples": [sample]
    }

    # create the trial
    ct = {
        "lead_organization_study_id": "test",
        "participants": [participant]
    }

    # create validator assert schemas are valid.
    validator = _fetch_validator("clinical_trial")
    validator.validate(ct)

def test_clinicaltrial_olink():

    # create the assay
    assays = {
        "olink": _sim_olink()
    }

    # create 2 aliquots
    aliquot1 = {
        "cimac_aliquot_id": "1234",
        "assay": assays
    }
    aliquot2 = {
        "cimac_aliquot_id": "1234",
        "assay": assays.copy()
    }

    # create the sample.
    sample1 = {
        "cimac_sample_id": "S1234",
        "site_sample_id": "blank",
        "aliquots": [aliquot1]
    }
    sample2 = {
        "cimac_sample_id": "SABCD",
        "site_sample_id": "blank",
        "aliquots": [aliquot2]
    }

    # create the participant
    participant1 = {
        "cimac_participant_id": "P1234",
        "trial_participant_id": "blank",
        "samples": [sample1]
    }
    participant2 = {
        "cimac_participant_id": "PABCD",
        "trial_participant_id": "blank",
        "samples": [sample2]
    }

    # create the trial
    ct = {
        "lead_organization_study_id": "test",
        "participants": [participant1, participant2]
    }

    # create validator assert schemas are valid.
    validator = _fetch_validator("clinical_trial")
    validator.validate(ct)