#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for JSON loading/validation utilities."""

import os
import json

import pytest
import jsonschema
import jsonpointer

from cidc_schemas.json_validation import (
    _map_refs,
    load_and_validate_schema,
    _load_dont_validate_schema,
    _resolve_refs,
    _Validator,
    InDocRefNotFoundError,
    RefResolutionError,
    format_validation_error,
)
from cidc_schemas.prism import PROTOCOL_ID_FIELD_NAME
from .constants import SCHEMA_DIR, TEST_SCHEMA_DIR


def test_validator_iter_errors_in_doc_ref():
    """Show that calling iter_errors directly leads to an assertion error"""
    validator = _Validator(
        {
            "$schema": "http://json-schema.org/draft-2020-12/schema#",
            "additionalProperties": False,
            "type": "object",
            "properties": {"a": {"type": "string", "in_doc_ref_pattern": "/a"}},
        }
    )

    valid_instance = {"a": "foo"}

    with pytest.raises(
        AssertionError, match="Please call _Validator.safe_iter_errors instead."
    ):
        list(validator.iter_errors(valid_instance))

    errors = list(validator.safe_iter_errors(valid_instance))
    assert len(errors) == 0


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

    shipment = {
        "account_number": "account_number",
        "assay_priority": "1",
        "assay_type": "Olink",
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

    # create some samples.
    sample1 = {
        "cimac_id": "CTTTPPP12.00",
        "parent_sample_id": "ssida",
        "collection_event_name": "Baseline",
        "type_of_primary_container": "Sodium heparin",
        "sample_location": "---",
        "type_of_sample": "Other",
        "sample_volume_units": "Other",
        "material_used": 1,
        "material_remaining": 0,
        "quality_of_sample": "Other",
        "box_number": "1",
    }
    sm_validator.validate(sample1)
    sample2 = {
        "cimac_id": "CTTTPPP12.00",
        "parent_sample_id": "ssidb",
        "collection_event_name": "Baseline",
        "type_of_primary_container": "Sodium heparin",
        "sample_location": "---",
        "type_of_sample": "Other",
    }
    sm_validator.validate(sample2)

    # create a bad participant, then make it good.
    participant = {
        "cimac_participant_id": "CTTTPPP",
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
        "allowed_collection_event_names": ["Baseline"],
        "allowed_cohort_names": ["Arm_Z"],
        "participants": [participant],
        "shipments": [shipment],
    }
    ct_validator.validate(clinical_trial)

    # make it fail
    participant.pop("cimac_participant_id")
    with pytest.raises(jsonschema.ValidationError):
        ct_validator.validate(clinical_trial)


def do_resolve(schema_path):
    with open(os.path.join(TEST_SCHEMA_DIR, schema_path)) as f:
        spec = json.load(f)
        return _resolve_refs(TEST_SCHEMA_DIR, spec, schema_path)


def test_resolve_refs():
    """Ensure that ref resolution can handle nested refs"""
    c = do_resolve("c.json")

    # One level of nesting
    b = do_resolve("b.json")
    assert b["properties"] == {
        "b_prop": c,
        "recursive_prop": {"$ref": "#/definitions/nested_arrays"},
    }

    # Two levels of nesting with a local ref that should *not* have been resolved
    a = do_resolve("a.json")
    assert a["properties"] == {"a_prop": b}

    # Two levels of nesting across different directories
    one = do_resolve("1.json")
    assert one["properties"] == {"1_prop": {"2_prop": {"3_prop": {"type": "string"}}}}

    with pytest.raises(RefResolutionError, match="invalid_ref.json"):
        do_resolve("invalid_ref.json")


def test_recursive_validations():
    validator = load_and_validate_schema(
        "a.json", schema_root=TEST_SCHEMA_DIR, return_validator=True
    )

    with pytest.raises(jsonschema.ValidationError, match="not of type 'array'"):
        validator.validate({"a_prop": {"recursive_prop": {}}})

    with pytest.raises(jsonschema.ValidationError, match="not of type 'array'"):
        validator.validate({"a_prop": {"recursive_prop": [{}]}})

    with pytest.raises(jsonschema.ValidationError, match="not of type 'array'"):
        validator.validate({"a_prop": {"recursive_prop": [[{}], [], [[]]]}})

    validator.validate({"a_prop": {"recursive_prop": [[[]], [], [[[[]]]]]}})


def test_get_values_for_path_pattern():
    v = _Validator({})
    # Absolute path, all strings
    assert v._get_values_for_path_pattern(
        "/a/b/c", {"a": {"b": {"c": "foo", "d": "bar"}}}
    ) == set([repr("foo")])
    # Absolute path, array index
    assert v._get_values_for_path_pattern(
        "/a/1/b", {"a": [{"b": "foo"}, {"b": "bar"}]}
    ) == set([repr("bar")])
    # Absolute path, dict with a key that looks like integer
    assert v._get_values_for_path_pattern(
        "/a/0/1", {"a": [{"1": "foo"}, {"1": "bar"}]}
    ) == set([repr("foo")])
    # Absolute path, integer property
    assert v._get_values_for_path_pattern("/a/1", {"a": {1: "foo", "b": "bar"}}) == set(
        [repr("foo")]
    )
    # Absolute path, non-primitive value
    assert v._get_values_for_path_pattern("/a", {"a": [1, 2, 3]}) == set(
        [repr([1, 2, 3])]
    )

    # Path with pattern matching, array
    assert v._get_values_for_path_pattern(
        "/a/*/b", {"a": [{"b": 1, "c": "foo"}, {"b": 2, "c": "foo"}]}
    ) == set([repr(1), repr(2)])
    # Path with pattern matching, dict
    assert v._get_values_for_path_pattern(
        "/a/*/b", {"a": {"buzz": {"b": 1, "c": "foo"}, "bazz": {"b": 2, "c": "foo"}}}
    ) == set([repr(1), repr(2)])
    # Path with pattern matching, nested
    assert v._get_values_for_path_pattern(
        "/a/*/b/*/c",
        {
            "a": [
                {"b": [{"c": 1}, {"c": 2}], "c": "foo"},
                {"b": {"buzz": {"c": 3}, "bazz": {"c": 4}}, "c": "foo"},
            ]
        },
    ) == set([repr(1), repr(2), repr(3), repr(4)])


def test_validate_in_doc_refs():
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

    instance = {"objs": [{"id": 1}, {"id": "something"}], "refs": [1, "something"]}
    v.validate(instance)
    with v._validation_context(instance):
        assert v._in_doc_refs_cache == {"/objs/*/id": {repr(1), repr("something")}}

    instance = {"objs": [{"id": 1}, {"id": "something"}], "refs": [1]}
    v.validate(instance)
    with v._validation_context(instance):
        assert v._in_doc_refs_cache == {"/objs/*/id": {repr(1), repr("something")}}

    assert 2 == len(
        [
            e
            for e in v.safe_iter_errors(
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


def test_load_ct_schema_speed(benchmark):
    def load():
        load_and_validate_schema("clinical_trial.json")

    benchmark.pedantic(load, rounds=3)


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
                                "items": {"type": "object", "required": ["id"]},
                            }
                        },
                        "required": ["records"],
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
                {"records": [{"id": i} for i in range(200, 400)]},
            ],
            "refs": list(range(400)),
        }

        # valid
        v.validate(instance)
        # invalid
        try:
            instance["refs"].append("no ref integrity :(")
            v.validate(instance)
        except jsonschema.exceptions.ValidationError:
            pass
        except:
            raise

    benchmark.pedantic(do_validation, rounds=3)


def test_special_keywords():

    # load the schema
    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "templates/assays/cytof_template.json")
    # we don't validate it because it's a template, not a schema
    schema = _load_dont_validate_schema(schema_path, schema_root)

    tmp1 = schema["properties"]["worksheets"]["Acquisition and Preprocessing"]
    tmp2 = tmp1["data_columns"]["Preprocessing"]["processed fcs filename"]

    assert "is_multi_artifact" not in tmp2
    assert "is_artifact" in tmp2


def test_format_validation_error():
    """Check that format_validation_error works as expected on different error scenarios."""
    validator = jsonschema.Draft7Validator(
        {
            "type": "object",
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "array", "items": {"type": "number"}},
                "c": {
                    "type": "object",
                    "properties": {
                        "foo": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["foo"],
                },
            },
            "required": ["a", "b", "c"],
        }
    )

    def format_error(instance: dict):
        try:
            validator.validate(instance)
        except jsonschema.ValidationError as e:
            return format_validation_error(e)

    valid_instance = {"a": "ok", "b": [1, 2, 3], "c": {"foo": ["a"]}}

    # Root-level property type error
    inst = {**valid_instance, "a": 1}
    err = format_error(inst)
    assert err == "error on a=1: 1 is not of type 'string'"

    # Array value type error
    inst = {**valid_instance, "b": [1, "oops", 2]}
    err = format_error(inst)
    assert err == "error on b[1]=oops: 'oops' is not of type 'number'"

    # Array inside nested object
    inst = {**valid_instance, "c": {"foo": [1]}}
    err = format_error(inst)
    assert err == "error on foo[0]=1: 1 is not of type 'string'"

    # Nest property missing
    inst = {**valid_instance, "c": {}}
    err = format_error(inst)
    assert err == "error on c={}: missing required property 'foo'"

    # Root-level property missing
    valid_instance.pop("a")
    err = format_error(valid_instance)
    assert (
        err
        == "error on [root]={'b': [1, 2, 3], 'c': {'foo': ['a']}}: missing required property 'a'"
    )


def test_iter_error_messages():
    """Smoke check that _Validator.iter_error_messages returns strings, not ValidationErrors."""
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    errs = list(validator.iter_error_messages({"protocol_identifier": "foo123"}))
    for err in errs:
        assert isinstance(err, str)


def test_load_subschema():
    """Test that the subschema loading option works as expected."""
    schema = load_and_validate_schema("clinical_trial.json")
    subschema = schema["properties"]["participants"]
    path = "properties/participants"

    assert subschema == load_and_validate_schema(f"clinical_trial.json#{path}")
    assert subschema == load_and_validate_schema(f"clinical_trial.json#/{path}")

    with pytest.raises(jsonpointer.JsonPointerException):
        load_and_validate_schema("clinical_trial.json#foo")
