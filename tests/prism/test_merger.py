"""Tests for generic merging functionality."""
import os
from unittest.mock import MagicMock

import pytest
import jsonschema
from jsonmerge import Merger

from cidc_schemas.prism import merger as prism_merger

from ..constants import TEST_DATA_DIR

# TODO: remove dependency on these tests
from .test_prism_cidc_data_model import (
    prismify_test_set,
    test_prism,
    test_prismify_olink_only,
)

#### MERGE STRATEGY TESTS ####
def test_throw_on_collision():
    """Test the custom ThrowOnCollision merge strategy"""
    schema = {
        "type": "object",
        "properties": {
            "l": {
                "type": "array",
                "items": {"cimac_id": {"type": "string"}, "a": {"type": "integer"}},
                "mergeStrategy": "arrayMergeById",
                "mergeOptions": {"idRef": "/cimac_id"},
            }
        },
    }

    merger = Merger(schema, strategies=prism_merger.PRISM_MERGE_STRATEGIES)

    # Identical values, no collision - no error
    base = {"l": [{"cimac_id": "c1", "a": 1}]}
    assert merger.merge(base, base)

    # Different values, collision - error
    head = {"l": [{"cimac_id": "c1", "a": 2}]}
    with pytest.raises(
        prism_merger.MergeCollisionException, match=r"1 \(current\) != 2 \(incoming\)"
    ):
        merger.merge(base, head)

    # Some identical and some different values - no error, proper merge
    base["l"].append({"cimac_id": "c2", "a": 2})
    head = {"l": [base["l"][0], {"cimac_id": "c3", "a": 3}]}

    assert merger.merge(base, head) == {"l": [*base["l"], head["l"][-1]]}


def test_overwrite_any():
    """Test that the alias for jsonmerge.strategies.Overwrite is set up properly"""
    schema = {
        "type": "object",
        "properties": {
            "a": {"type": "object", "mergeStrategy": "overwriteAny"},
            "b": {"type": "number"},
        },
    }

    merger = Merger(schema, strategies=prism_merger.PRISM_MERGE_STRATEGIES)

    # Updates to "a" should be allowed
    base = {"a": {"foo": "bar"}, "b": 1}
    head = {"a": {"foo": "buzz"}, "b": 1}
    assert merger.merge(base, head) == head

    # Updates to "b" should not be allowed
    head["b"] = 2
    with pytest.raises(
        prism_merger.MergeCollisionException, match=r"1 \(current\) != 2 \(incoming\)"
    ):
        merger.merge(base, head)


def test_set_data_format_edge_cases(monkeypatch):
    def mock_iter_errors(errs):
        validator = MagicMock()
        validator.iter_errors.return_value = errs
        load_and_val = MagicMock()
        load_and_val.return_value = validator
        monkeypatch.setattr(
            "cidc_schemas.json_validation.load_and_validate_schema", load_and_val
        )

    # _set_data_format bypasses exceptions that aren't jsonschema.exceptions.ValidationError instances.
    mock_iter_errors([Exception("non-validation error")])
    artifact = {}
    prism_merger._set_data_format({}, artifact)
    assert artifact["data_format"] == "[NOT SET]"

    # _set_data_format bypasses validation errors not pertaining to the "data_format" field
    val_error = jsonschema.exceptions.ValidationError("")
    val_error.validator = "const"
    val_error.path = ["some_path"]
    artifact = {}
    prism_merger._set_data_format({}, artifact)
    assert artifact["data_format"] == "[NOT SET]"

    # _set_data_format bypasses validation errors on unrelated fields
    val_error = jsonschema.exceptions.ValidationError("")
    val_error.validator = "const"
    val_error.path = ["data_format"]
    val_error.instance = "unrelated instance"
    mock_iter_errors([val_error])
    artifact = {}
    prism_merger._set_data_format({}, artifact)
    assert artifact["data_format"] == "[NOT SET]"


#### END MERGE STRATEGY TESTS ####

#### EXTRA METADATA TESTS ####


@pytest.fixture
def npx_file_path():
    return os.path.join(TEST_DATA_DIR, "olink", "olink_assay_1_NPX.xlsx")


@pytest.fixture
def npx_combined_file_path():
    return os.path.join(TEST_DATA_DIR, "olink", "olink_assay_combined.xlsx")


@pytest.fixture
def elisa_test_file_path():
    return os.path.join(TEST_DATA_DIR, "elisa_test_file.xlsx")


def test_merge_artfiact_extra_metadata_unsupported_assay():
    """Ensure merge_artifact_extra_metadata fails gracefully for unsupported assays"""
    assay_hint = "foo"
    with pytest.raises(
        Exception, match=f"Assay {assay_hint} does not support extra metadata"
    ):
        prism_merger.merge_artifact_extra_metadata({}, "", assay_hint, None)


def test_merge_extra_metadata_olink(npx_file_path, npx_combined_file_path):
    xlsx, template = list(prismify_test_set("olink"))[0]
    ct, file_infos = test_prismify_olink_only(xlsx, template)

    for finfo in file_infos:
        if finfo.metadata_availability:
            if "combined" in finfo.local_path:
                local_path = npx_combined_file_path
            else:
                local_path = npx_file_path

            with open(local_path, "rb") as npx_file:
                prism_merger.merge_artifact_extra_metadata(
                    ct, finfo.upload_placeholder, "olink", npx_file
                )

    study = ct["assays"]["olink"]["study"]
    files = ct["assays"]["olink"]["records"][0]["files"]

    assert set(files["assay_npx"]["samples"]) == {
        "CTTTP01A1.00",
        "CTTTP02A1.00",
        "CTTTP03A1.00",
        "CTTTP04A1.00",
    }
    assert set(study["study_npx"]["samples"]) == {
        "CTTTP01A1.00",
        "CTTTP02A1.00",
        "CTTTP03A1.00",
        "CTTTP04A1.00",
        "CTTTP05A1.00",
        "CTTTP06A1.00",
        "CTTTP07A1.00",
        "CTTTP08A1.00",
        "CTTTP09A1.00",
    }


def test_merge_extra_metadata_elisa(elisa_test_file_path):
    xlsx, template = list(prismify_test_set("elisa"))[0]
    ct, file_infos = test_prism(xlsx, template)

    for finfo in file_infos:
        if finfo.metadata_availability:

            with open(elisa_test_file_path, "rb") as elisa_file:
                prism_merger.merge_artifact_extra_metadata(
                    ct, finfo.upload_placeholder, "elisa", elisa_file
                )

    artifact = ct["assays"]["elisa"][0]["assay_xlsx"]

    # TODO antibodies

    assert artifact["data_format"] == "ELISA"
    assert artifact["number_of_samples"] == 7
    assert set(artifact["samples"]) == {
        "CTTTP01A1.00",
        "CTTTP01A2.00",
        "CTTTP01A3.00",
        "CTTTP02A1.00",
        "CTTTP02A2.00",
        "CTTTP02A3.00",
        "CTTTP02A4.00",
    }


def test_parse_npx_invalid(npx_file_path):
    # test the parse function by passing a file path
    with pytest.raises(TypeError):
        samples = prism_merger.parse_npx(npx_file_path)


def test_parse_npx_single(npx_file_path):
    # test the parse function
    f = open(npx_file_path, "rb")
    samples = prism_merger.parse_npx(f)

    assert samples["number_of_samples"] == 4
    assert set(samples["samples"]) == {
        "CTTTP01A1.00",
        "CTTTP02A1.00",
        "CTTTP03A1.00",
        "CTTTP04A1.00",
    }


def test_parse_npx_merged(npx_combined_file_path):
    # test the parse function
    f = open(npx_combined_file_path, "rb")
    samples = prism_merger.parse_npx(f)

    assert samples["number_of_samples"] == 9

    assert set(samples["samples"]) == {
        "CTTTP01A1.00",
        "CTTTP02A1.00",
        "CTTTP03A1.00",
        "CTTTP04A1.00",
        "CTTTP05A1.00",
        "CTTTP06A1.00",
        "CTTTP07A1.00",
        "CTTTP08A1.00",
        "CTTTP09A1.00",
    }


def test_parse_elisa_invalid(elisa_test_file_path):
    # test the parse function by passing a file path
    with pytest.raises(TypeError):
        samples = prism_merger.parse_elisa(elisa_test_file_path)


def test_parse_elisa_single(elisa_test_file_path):
    # test the parse function
    f = open(elisa_test_file_path, "rb")
    samples = prism_merger.parse_elisa(f)

    assert samples["number_of_samples"] == 7
    assert set(samples["samples"]) == {
        "CTTTP01A1.00",
        "CTTTP01A2.00",
        "CTTTP01A3.00",
        "CTTTP02A1.00",
        "CTTTP02A2.00",
        "CTTTP02A3.00",
        "CTTTP02A4.00",
    }


#### END EXTRA METADATA TESTS ####
