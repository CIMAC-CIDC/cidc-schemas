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


def test_trial_core():

    # load and validate schema.
    schema_root = SCHEMA_DIR
    ct_schema_path = os.path.join(SCHEMA_DIR, "clinical_trial.json")
    pt_schema_path = os.path.join(SCHEMA_DIR, "participant.json")
    sm_schema_path = os.path.join(SCHEMA_DIR, "sample.json")
    al_schema_path = os.path.join(SCHEMA_DIR, "aliquot.json")

    ct_schema = load_and_validate_schema(ct_schema_path, schema_root)
    pt_schema = load_and_validate_schema(pt_schema_path, schema_root)
    sm_schema = load_and_validate_schema(sm_schema_path, schema_root)
    al_schema = load_and_validate_schema(al_schema_path, schema_root)

    # create validator assert schemas are valid.
    ct_validator = jsonschema.Draft7Validator(ct_schema)
    ct_validator.check_schema(ct_schema)

    pt_validator = jsonschema.Draft7Validator(pt_schema)
    pt_validator.check_schema(pt_schema)

    sm_validator = jsonschema.Draft7Validator(sm_schema)
    sm_validator.check_schema(sm_schema)

    al_validator = jsonschema.Draft7Validator(al_schema)
    al_validator.check_schema(al_schema)

    # create some aliquots.
    shipment = {"request": "DFCI"}
    aliquot1 = {
        "cimac_aliquot_id": "c1d1"
    }

    aliquot2 = {
        "cimac_aliquot_id": "c1d2"
    }
    al_validator.validate(aliquot1)
    al_validator.validate(aliquot2)

    # create some samples.
    sample1 = {
        "cimac_sample_id": "csid1",
        "site_sample_id": "ssida",
        "aliquots": [aliquot1]
    }
    sample2 = {
        "cimac_sample_id": "csid12",
        "site_sample_id": "ssidb",
        "aliquots": [aliquot2]
    }
    sm_validator.validate(sample1)
    sm_validator.validate(sample2)

    # create a bad participant, then make it good.
    participant = {
        "cimac_participant_id": "cpid_1",
        "trial_participant_id": "tpid_a"
    }
    with pytest.raises(jsonschema.ValidationError):
        pt_validator.validate(participant)

    # add samples to the participant.
    participant["samples"] = [sample1, sample2]
    pt_validator.validate(participant)

    # validate the positive version works.
    clinical_trial = {
        "lead_organization_study_id": "trial1",
        "participants": [participant],
        "shipments": [shipment]
    }
    ct_validator.validate(clinical_trial)

    # make it fail
    participant.pop('cimac_participant_id')
    with pytest.raises(jsonschema.ValidationError):
        ct_validator.validate(clinical_trial)


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
