#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for JSON loading/validation utilities."""
import os
import pytest
import jsonschema

from cidc_schemas.json_validation import _map_refs, load_and_validate_schema
from .constants import SCHEMA_DIR, ROOT_DIR

def test_map_refs():
    spec = {
        'a': {
            '$ref': 'foo'
        },
        'b': [
            {'$ref': 'foo'}
        ]
    }

    target = {
        'a': 'FOO',
        'b': ['FOO']
    }

    assert _map_refs(spec, lambda ref: ref.upper()) == target

def test_trial_core():

    # load and validate schema.
    schema_root = SCHEMA_DIR
    ct_schema_path = os.path.join(SCHEMA_DIR, "clinical_trial.json")
    pt_schema_path = os.path.join(SCHEMA_DIR, "participant.json")
    sm_schema_path = os.path.join(SCHEMA_DIR, "sample.json")

    ct_schema = load_and_validate_schema(ct_schema_path, schema_root)
    pt_schema = load_and_validate_schema(pt_schema_path, schema_root)
    sm_schema = load_and_validate_schema(sm_schema_path, schema_root)

    # create validator assert schemas are valid.
    ct_validator = jsonschema.Draft7Validator(ct_schema)
    ct_validator.check_schema(ct_schema)

    pt_validator = jsonschema.Draft7Validator(pt_schema)
    pt_validator.check_schema(pt_schema)

    sm_validator = jsonschema.Draft7Validator(sm_schema)
    sm_validator.check_schema(sm_schema)

    # create some samples
    sample1 = {
      "cimac_sample_id": "csid1",
      "site_sample_id": "ssida"
    }
    sample2 = {
      "cimac_sample_id": "csid12",
      "site_sample_id": "ssidb"
    }
    #sm_validator.validate(sample1)
    #sm_validator.validate(sample2)

    # create a bad participant, then make it good.
    participant = {
      "cimac_participant_id": "cpid_1", 
    }
    #with pytest.raises(jsonschema.ValidationError):
    #  pt_validator.validate(participant)    

    participant['trial_participant_id'] = 'tpid_a'
    #pt_validator.validate(participant)

    # add samples to the participant.
    participant["samples"] = [sample1, sample2]
    #pt_validator.validate(participant)

    # validate the positive version works.
    clinical_trial = {
      "lead_organization_study_id": "trial1",
      "participants": [participant]
    }
    ct_validator.validate(clinical_trial)

    # make it fail 
    participant.pop('trial_participant_id')
    with pytest.raises(jsonschema.ValidationError):
      ct_validator.validate(clinical_trial)
    