"""Tests for generic merging functionality."""
from copy import deepcopy
from uuid import uuid4
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
    invalid_npx_file_path,
    elisa_file_path_1,
    single_npx_metadata,
    combined_npx_metadata,
    elisa_metadata_1,
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
        match="mismatch of weight=2 and weight=333 in p_id='c2'",
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
        match="mismatch of weight=2 and weight=333"
        " in sample_id='c1' participant_id='p1'",
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
        prism_merger.MergeCollisionException, match="mismatch of b=1.*and b=2"
    ):
        merger.merge(base, head)


#### END MERGE STRATEGY TESTS ####

#### MERGER TESTS ####


def test_merge_clinical_trial_metadata_invalid_target():
    """Ensure `merge_clinical_trial_metadata` catches expected corner cases."""
    valid_patch = {PROTOCOL_ID_FIELD_NAME: "test_prism_trial_id"}

    # invalid_target = {"foo": "bar"}
    # with pytest.raises(
    #     prism_merger.InvalidMergeTargetException, match="target is invalid"
    # ):
    #     prism_merger.merge_clinical_trial_metadata(valid_patch, invalid_target)

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


@pytest.fixture
def ct_and_artifacts():
    num_artifacts = 500

    def make_artifacts():
        return [
            prism_merger.ArtifactInfo(
                artifact_uuid=str(uuid4()),
                object_url="a/b",
                upload_type="",
                file_size_bytes=0,
                uploaded_timestamp="",
                crc32c_hash="foo",
            )
            for _ in range(num_artifacts)
        ]

    artifacts = make_artifacts()
    ct = {
        "a": {
            "b": [
                {"upload_placeholder": a.artifact_uuid}
                for a in artifacts[: num_artifacts // 4]
            ],
            "c": [
                {
                    "d": [
                        {"upload_placeholder": a.artifact_uuid}
                        for a in artifacts[num_artifacts // 4 : num_artifacts // 2]
                    ]
                },
                {
                    "d": [
                        {"upload_placeholder": a.artifact_uuid}
                        for a in artifacts[num_artifacts // 2 : num_artifacts * 3 // 4]
                    ],
                    "e": {
                        "f": [
                            {"upload_placeholder": a.artifact_uuid}
                            for a in artifacts[num_artifacts * 3 // 4 :]
                        ]
                    },
                },
            ],
        }
    }

    return ct, artifacts


def test_merge_artifacts_speed(benchmark, ct_and_artifacts):
    benchmark(prism_merger.merge_artifacts, *ct_and_artifacts)


def merge_one_by_one(ct, artifacts):
    updated_artifacts = []
    for artifact in artifacts:
        ct, *updated_artifact = prism_merger.merge_artifact(ct, *artifact)
        updated_artifacts.append(tuple(updated_artifact))
    return ct, updated_artifacts


def test_merge_artifact_speed(benchmark, ct_and_artifacts):
    benchmark(merge_one_by_one, *ct_and_artifacts)


def test_merge_artifacts_smoketest(ct_and_artifacts):
    """
    Ensure merge_artifacts produces the same result as repeated calls to merge_artifact
    """
    ct, artifacts = ct_and_artifacts
    ct_batch, artifacts_batch = prism_merger.merge_artifacts(deepcopy(ct), artifacts)
    ct_1by1, artifacts_1by1 = merge_one_by_one(deepcopy(ct), artifacts)
    assert ct_batch == ct_1by1
    assert artifacts_batch == artifacts_1by1


#### END MERGER TESTS ####

#### EXTRA METADATA TESTS ####


def test_merge_artifact_extra_metadata_exc(monkeypatch):
    """Ensure merge_artifact_extra_metadata fails gracefully for unsupported assays
    Also raises clearer error if parser raises ValueError, but not TypeError"""
    assay_hint = "foo"
    with pytest.raises(
        ValueError, match=f"Assay {assay_hint} does not support extra metadata"
    ):
        prism_merger.merge_artifact_extra_metadata({}, "", assay_hint, None)

    artifact_uuid = "uuid-1"
    fake_parsers = {"olink": MagicMock(), "testing": MagicMock()}
    fake_parsers["olink"].side_effect = ValueError("disappears")
    fake_parsers["testing"].side_effect = TypeError("this goes through")

    # test wrapping ValueError
    with monkeypatch.context():
        monkeypatch.setattr(
            "cidc_schemas.prism.merger.EXTRA_METADATA_PARSERS", fake_parsers
        )

        with pytest.raises(
            ValueError,
            match=f"Assay {artifact_uuid} cannot be parsed for olink metadata",
        ):
            with open(invalid_npx_file_path, "rb") as f:
                prism_merger.merge_artifact_extra_metadata(
                    {}, artifact_uuid, "olink", f
                )

    # doesn't wrap TypeErrors; None is not a BinaryIO
    with monkeypatch.context():
        monkeypatch.setattr(
            "cidc_schemas.prism.merger.EXTRA_METADATA_PARSERS", fake_parsers
        )

        with pytest.raises(TypeError, match=r"this goes through"):
            prism_merger.merge_artifact_extra_metadata(
                {}, artifact_uuid, "testing", None
            )


# upload placeholder shorthand
up = lambda uuid: {"upload_placeholder": uuid}


@pytest.fixture
def olink_ct_metadata():
    return {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "olink": {
                "batches": [
                    {
                        "records": [
                            {
                                "files": {
                                    "assay_npx": up("npx_1"),
                                    "assay_raw_ct": up("ct_1"),
                                }
                            }
                        ]
                    }
                ],
                "study": {"npx_file": up("study_npx")},
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
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path=npx_combined_file_path,
            gs_key="",
            upload_placeholder="study_npx",
            metadata_availability=True,
            allow_empty=False,
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

    study_npx = olink_ct_metadata["assays"]["olink"]["study"]["npx_file"]
    assay_npx = olink_ct_metadata["assays"]["olink"]["batches"][0]["records"][0][
        "files"
    ]["assay_npx"]

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
            local_path=elisa_file_path_1,
            gs_key="",
            upload_placeholder="elisa_file",
            metadata_availability=True,
            allow_empty=False,
        )
    ]


def test_merge_extra_metadata_elisa(elisa_ct_metadata, elisa_file_infos):
    _do_extra_metadata_merge(elisa_ct_metadata, elisa_file_infos, "elisa")

    artifact = elisa_ct_metadata["assays"]["elisa"][0]["assay_xlsx"]

    # TODO antibodies
    for key in ["samples", "number_of_samples"]:
        assert artifact[key] == elisa_metadata_1[key]


#### END EXTRA METADATA TESTS ####
