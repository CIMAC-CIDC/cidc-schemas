"""Tests for generic merging functionality."""
import os
from unittest.mock import MagicMock

import pytest
import jsonschema
from jsonmerge import Merger

from cidc_schemas.prism import merger as prism_merger
from cidc_schemas.prism.core import LocalFileUploadEntry

from .test_extra_metadata import npx_file_path, npx_combined_file_path, elisa_file_path

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

    study = olink_ct_metadata["assays"]["olink"]["study"]
    files = olink_ct_metadata["assays"]["olink"]["records"][0]["files"]

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


#### END EXTRA METADATA TESTS ####
