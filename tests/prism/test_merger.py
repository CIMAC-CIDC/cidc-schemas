"""Tests for generic merging functionality."""
import os
from unittest.mock import MagicMock

import pytest
import jsonschema
from jsonmerge import Merger

from cidc_schemas.prism import merger as prism_merger
from cidc_schemas.prism.core import LocalFileUploadEntry
from cidc_schemas.prism.constants import PROTOCOL_ID_FIELD_NAME

from .test_extra_metadata import (
    npx_file_path,
    npx_combined_file_path,
    elisa_file_path,
    single_npx_metadata,
    combined_npx_metadata,
    elisa_metadata,
)

#### MERGE STRATEGY TESTS ####
def test_throw_on_mismatch():
    """Test the custom ThrowOnMismatch merge strategy"""
    schema = {
        "type": "object",
        "properties": {
            "participants": {
                "type": "array",
                "items": {"p_id": {"type": "string"}, "weight": {"type": "integer"}},
                "mergeStrategy": "arrayMergeById",
                "mergeOptions": {"idRef": "/p_id"},
            }
        },
    }

    merger = Merger(schema, strategies=prism_merger.PRISM_MERGE_STRATEGIES)

    # Identical values, no mismatch - no error
    base = {"participants": [{"p_id": "c1", "weight": 1}, {"p_id": "c2", "weight": 2}]}
    assert merger.merge(base, base)

    # Different values, mismatch - error
    head = {
        "participants": [{"p_id": "c2", "weight": 333}, {"p_id": "c3", "weight": 3}]
    }
    with pytest.raises(
        prism_merger.MergeCollisionException,
        match="mismatch of incoming weight=333 with already saved weight=2 in participants/p_id=c2",
    ):
        merger.merge(base, head)

    # Some identical and some different values - no error, proper merge
    base["participants"].append({"p_id": "c2", "weight": 2})
    head = {"participants": [base["participants"][0], {"p_id": "c3", "weight": 3}]}

    assert merger.merge(base, head) == {
        "participants": [*base["participants"], head["participants"][-1]]
    }


def test_throw_on_mismatch_context():
    """Test extra context from arrayMergeById for ThrowOnMismatch"""
    schema = {
        "type": "object",
        "properties": {
            "participants": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "participant_id": {"type": "string"},
                        "samples": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "sample_id": {"type": "string"},
                                    "weight": {"type": "integer"},
                                },
                            },
                            "mergeStrategy": "arrayMergeById",
                            "mergeOptions": {"idRef": "/sample_id"},
                        },
                    },
                },
                "mergeStrategy": "arrayMergeById",
                "mergeOptions": {"idRef": "/participant_id"},
            }
        },
    }

    merger = Merger(schema, strategies=prism_merger.PRISM_MERGE_STRATEGIES)

    # Identical values, no collision - no error
    base = {
        "participants": [
            {"participant_id": "p1", "samples": [{"sample_id": "c1", "weight": 2}]}
        ]
    }
    assert merger.merge(base, base)

    # Different values, collision - error
    head = {
        "participants": [
            {"participant_id": "p1", "samples": [{"sample_id": "c1", "weight": 333}]}
        ]
    }
    with pytest.raises(
        prism_merger.MergeCollisionException,
        match="mismatch of incoming weight=333 with already saved weight=2"
        " in samples/sample_id=c1 in participants/participant_id=p1",
    ):
        merger.merge(base, head)


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

    # Updates to "b" still should not be allowed
    head["b"] = 2
    with pytest.raises(
        prism_merger.MergeCollisionException,
        match="mismatch of incoming b=2 with already saved b=1",
    ):
        merger.merge(base, head)


def test_set_data_format_edge_cases(monkeypatch):
    def mock_iter_errors(errs):
        validator = MagicMock()
        validator.iter_errors.return_value = errs
        load_and_val = MagicMock()
        load_and_val.return_value = validator
        monkeypatch.setattr(prism_merger, "load_and_validate_schema", load_and_val)

    # _set_data_format bypasses exceptions that aren't jsonschema.exceptions.ValidationError instances.
    mock_iter_errors([Exception("non-validation error")])
    artifact = {}
    prism_merger._set_data_format({}, artifact)
    assert artifact["data_format"] == "[NOT SET]"

    # _set_data_format bypasses validation errors not pertaining to the "data_format" field
    val_error = jsonschema.exceptions.ValidationError("")
    val_error.validator = "const"
    val_error.path = ["some_path"]
    mock_iter_errors([val_error])
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

#### MERGER TESTS ####


def test_merge_clinical_trial_metadata_invalid_target():
    """Ensure `merge_clinical_trial_metadata` catches expected corner cases."""
    valid_patch = {PROTOCOL_ID_FIELD_NAME: "test_prism_trial_id"}

    invalid_target = {"foo": "bar"}
    with pytest.raises(
        prism_merger.InvalidMergeTargetException, match="target is invalid"
    ):
        prism_merger.merge_clinical_trial_metadata(valid_patch, invalid_target)

    wrong_trial_id_target = {
        PROTOCOL_ID_FIELD_NAME: "foobar",
        "participants": [],
        "allowed_cohort_names": [],
        "allowed_collection_event_names": [],
    }
    with pytest.raises(
        prism_merger.InvalidMergeTargetException, match="merge trials with different"
    ):
        prism_merger.merge_clinical_trial_metadata(valid_patch, wrong_trial_id_target)


#### END MERGER TESTS ####

#### EXTRA METADATA TESTS ####


def test_merge_artfiact_extra_metadata_unsupported_assay():
    """Ensure merge_artifact_extra_metadata fails gracefully for unsupported assays"""
    assay_hint = "foo"
    with pytest.raises(
        Exception, match=f"Assay {assay_hint} does not support extra metadata"
    ):
        prism_merger.merge_artifact_extra_metadata({}, "", assay_hint, None)


# upload placeholder shorthand
up = lambda uuid: {"upload_placeholder": uuid}


@pytest.fixture
def olink_ct_metadata():
    return {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "olink": {
                "records": [
                    {"files": {"assay_npx": up("npx_1"), "assay_raw_ct": up("ct_1")}}
                ],
                "study": {"study_npx": up("study_npx")},
            }
        },
    }


@pytest.fixture
def olink_file_infos():
    return [
        LocalFileUploadEntry(
            local_path=npx_file_path,
            gs_key="",
            upload_placeholder="npx_1",
            metadata_availability=True,
        ),
        LocalFileUploadEntry(
            local_path=npx_combined_file_path,
            gs_key="",
            upload_placeholder="study_npx",
            metadata_availability=True,
        ),
    ]


def _do_extra_metadata_merge(ct, file_infos, upload_type):
    for finfo in file_infos:
        with open(finfo.local_path, "rb") as data_file:
            prism_merger.merge_artifact_extra_metadata(
                ct, finfo.upload_placeholder, upload_type, data_file
            )


def test_merge_extra_metadata_olink(olink_ct_metadata, olink_file_infos):
    _do_extra_metadata_merge(olink_ct_metadata, olink_file_infos, "olink")

    study_npx = olink_ct_metadata["assays"]["olink"]["study"]["study_npx"]
    assay_npx = olink_ct_metadata["assays"]["olink"]["records"][0]["files"]["assay_npx"]

    assert assay_npx["data_format"] == "NPX"
    assert study_npx["data_format"] == "NPX"
    for key in ["samples", "number_of_samples"]:
        assert assay_npx[key] == single_npx_metadata[key]
        assert study_npx[key] == combined_npx_metadata[key]


@pytest.fixture
def elisa_ct_metadata():
    return {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {"elisa": [{"assay_xlsx": up("elisa_file")}]},
    }


@pytest.fixture
def elisa_file_infos():
    return [
        LocalFileUploadEntry(
            local_path=elisa_file_path,
            gs_key="",
            upload_placeholder="elisa_file",
            metadata_availability=True,
        )
    ]


def test_merge_extra_metadata_elisa(elisa_ct_metadata, elisa_file_infos):
    _do_extra_metadata_merge(elisa_ct_metadata, elisa_file_infos, "elisa")

    artifact = elisa_ct_metadata["assays"]["elisa"][0]["assay_xlsx"]

    # TODO antibodies
    assert artifact["data_format"] == "ELISA"
    for key in ["samples", "number_of_samples"]:
        assert artifact[key] == elisa_metadata[key]


#### END EXTRA METADATA TESTS ####
