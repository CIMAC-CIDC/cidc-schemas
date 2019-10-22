#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for JSON loading/validation utilities."""

import os
import json

import pytest
import jsonschema

from cidc_schemas.json_validation import (
    _map_refs,
    load_and_validate_schema,
    _resolve_refs,
    _Validator,
    InDocRefNotFoundError,
)
from cidc_schemas.prism import PROTOCOL_ID_FIELD_NAME
from .constants import SCHEMA_DIR, ROOT_DIR, TEST_SCHEMA_DIR


def test_map_refs():
    ref_spec = {"a": {"$ref": "foo"}, "b": [{"$ref": "foo"}]}
    mapped_refs = _map_refs(ref_spec.copy(), lambda ref: ref.upper())
    assert mapped_refs == {"a": "FOO", "b": ["FOO"]}

    # Fields with $ref in their values should not contain other keys
    ref_spec["a"]["extra"] = "blah"
    with pytest.raises(Exception, match="should not contain"):
        _map_refs(ref_spec, lambda ref: ref.upper())

    type_ref_spec = {"a": {"type_ref": "foo", "extra": "prop"}}
    mapped_spec = _map_refs(type_ref_spec, lambda _: {"a": "b"})
    assert mapped_spec == {"a": {"a": "b", "type_ref": "foo", "extra": "prop"}}


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
    shipment = {
        "account_number": "account_number",
        "assay_priority": "1",
        "assay_type": "Olink",
        "box_number": 1,
        "courier": "USPS",
        "date_received": "date_received",
        "date_shipped": "date_shipped",
        "manifest_id": "manifest_id",
        "quality_of_shipment": "Specimen shipment received in good condition",
        "ship_from": "ship_from",
        "ship_to": "ship_to",
        "shipping_condition": "Ice_Pack",
        "tracking_number": "tracking_number",
        "receiving_party": "MDA_Wistuba",
    }
    aliquot1 = {
        "slide_number": "99",
        "sample_volume_units": "Other",
        "material_used": 1,
        "material_remaining": 0,
        "quality_of_shipment": "Other",
        "aliquot_replacement": "N/A",
        "aliquot_status": "Other",
    }
    al_validator.validate(aliquot1)

    aliquot2 = {
        "slide_number": "98",
        "sample_volume_units": "Other",
        "material_used": 1,
        "material_remaining": 0,
        "quality_of_shipment": "Other",
        "aliquot_replacement": "N/A",
        "aliquot_status": "Other",
    }
    al_validator.validate(aliquot2)

    # create some samples.
    sample1 = {
        "cimac_id": "CM-TRIA-PART-12",
        "parent_sample_id": "ssida",
        "aliquots": [aliquot1],
        "collection_event_name": "Baseline",
        "type_of_primary_container":  "Sodium heparin",
        "sample_location": "---",
        "type_of_sample": "Other",
        "specimen_format": "Other",
        "genomic_source": "Normal",
    }
    sm_validator.validate(sample1)
    sample2 = {
        "cimac_id": "CM-TRIA-PART-12",
        "parent_sample_id": "ssidb",
        "aliquots": [aliquot2],
        "collection_event_name": "Baseline",
        "type_of_primary_container":  "Sodium heparin",
        "sample_location": "---",
        "type_of_sample": "Other",
        "specimen_format": "Other",
        "genomic_source": "Normal",
    }
    sm_validator.validate(sample2)

    # create a bad participant, then make it good.
    participant = {
        "cimac_participant_id": "CM-TRIA-PART",
        "participant_id": "tpid_a",
        "cohort_name": "Arm_Z",
    }
    with pytest.raises(jsonschema.ValidationError):
        pt_validator.validate(participant)

    # add samples to the participant.
    participant["samples"] = [sample1, sample2]
    pt_validator.validate(participant)

    # validate the positive version works.
    clinical_trial = {
        PROTOCOL_ID_FIELD_NAME: "trial1",
        "participants": [participant],
        "shipments": [shipment],
    }
    ct_validator.validate(clinical_trial)

    # make it fail
    participant.pop("cimac_participant_id")
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
    assert one["properties"] == {"1_prop": {"2_prop": {"3_prop": {"type": "string"}}}}

def test_get_values_for_path_pattern():
    v = _Validator({})
    # Absolute path, all strings
    assert v._get_values_for_path_pattern("/a/b/c", {"a": {"b": {"c": "foo", "d": "bar"}}}) == set([repr("foo")])
    # Absolute path, array index
    assert v._get_values_for_path_pattern("/a/1/b", {"a": [{"b": "foo"}, {"b": "bar"}]}) == set([repr("bar")])
    # Absolute path, dict with a key that looks like integer
    assert v._get_values_for_path_pattern("/a/0/1", {"a": [{"1": "foo"}, {"1": "bar"}]}) == set([repr("foo")])
    # Absolute path, integer property
    assert v._get_values_for_path_pattern("/a/1", {"a": {1: "foo", "b": "bar"}}) == set([repr("foo")])
    # Absolute path, non-primitive value
    assert v._get_values_for_path_pattern("/a", {"a": [1, 2, 3]} ) == set([repr([1,2,3])])

    # Path with pattern matching, array
    assert v._get_values_for_path_pattern(
        "/a/*/b", 
        {"a": [{"b": 1, "c": "foo"}, {"b": 2, "c": "foo"}]}
    ) == set([repr(1), repr(2)])
    # Path with pattern matching, dict
    assert v._get_values_for_path_pattern(
        "/a/*/b", 
        {"a": {"buzz": {"b": 1, "c": "foo"}, "bazz": {"b": 2, "c": "foo"}}}
    ) == set([repr(1), repr(2)])
    # Path with pattern matching, nested
    assert v._get_values_for_path_pattern(
        "/a/*/b/*/c",
        {
            "a": [
                {
                    "b": [{"c": 1}, {"c": 2}], 
                    "c": "foo"
                }, 
                {
                    "b": {"buzz": {"c": 3}, "bazz": {"c": 4}}
                    , "c": "foo"
                }
            ]
        }
    ) == set([repr(1), repr(2), repr(3), repr(4)])


def test_validate_in_doc_refs():
    doc = {"objs": [{"id": "1"}, {"id": "something"}]}

    v = empty_schema_validator = _Validator({})
    in_doc_refs_cache = {}
    assert True == v._ensure_in_doc_ref("something", "/objs/*/id", doc, in_doc_refs_cache)

    assert True == v._ensure_in_doc_ref("1", "/objs/*/id", doc, in_doc_refs_cache)

    assert True == v._ensure_in_doc_ref("1", "/*/*/id", doc, in_doc_refs_cache)

    assert False == v._ensure_in_doc_ref("something_else", "/objs/*/id", doc, in_doc_refs_cache)

    assert False == v._ensure_in_doc_ref("something", "/objs", doc, in_doc_refs_cache)

    v = _Validator(
        {
            "properties": {
                "objs": {
                    "type:": "array",
                    "items": {"type": "object", "required": ["id"]},
                },
                "refs": {
                    "type:": "array",
                    "items": {"in_doc_ref_pattern": "/objs/*/id"},
                },
            }
        }
    )

    v.validate({"objs": [{"id": 1}, {"id": "something"}], "refs": [1, "something"]})

    v.validate({"objs": [{"id": 1}, {"id": "something"}], "refs": [1]})

    assert 2 == len(
        [
            e
            for e in v.iter_errors(
                {
                    "objs": [{"id": 1}, {"id": "something"}],
                    "refs": [2, "something", "else"],
                }
            )
            if isinstance(e, InDocRefNotFoundError)
        ]
    )

    with pytest.raises(InDocRefNotFoundError):
        v.validate({"objs": [], "refs": ["anything"]})

def test_validator_speed(benchmark):
    """Basic referential integrity validation speed test"""
    v = _Validator(
        {
            "properties": {
                "objs": {
                    "type:": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "records": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id"]
                                },
                            }
                        },
                        "required": ["records"]
                    },
                },
                "refs": {
                    "type:": "array",
                    "items": {"in_doc_ref_pattern": "/objs/*/records/*/id"},
                },
            }
        }
    )

    def do_validation():
        instance = {
            "objs": [
                {"records": [{"id": i} for i in range(200)]}, 
                {"records": [{"id": i} for i in range(200, 400)]}
            ],
            "refs": list(range(400))
        }

        # valid
        v.validate(instance)
        # invalid
        try:
            instance['refs'].append("no ref integrity :(")
            v.validate(instance)
        except jsonschema.exceptions.ValidationError:
            pass
        except:
            raise

    benchmark.pedantic(do_validation, rounds=5)

def test_special_keywords():

    # load the schema
    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "templates/metadata/cytof_template.json")
    schema = load_and_validate_schema(schema_path, schema_root)

    tmp1 = schema["properties"]["worksheets"]["Acquisition and Preprocessing"]
    tmp2 = tmp1["data_columns"]["Preprocessing"]["processed fcs filename"]

    assert "is_multi_artifact" not in tmp2
    assert "is_artifact" in tmp2
