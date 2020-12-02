import pytest

from cidc_schemas.migrations import (
    _follow_path,
    v0_10_0_to_v0_10_2,
    MigrationError,
    v0_10_2_to_v0_11_0,
    v0_15_2_to_v0_15_3,
    v0_21_1_to_v0_22_0,
    _ENCRYPTED_FIELD_LEN,
    v0_23_0_to_v0_23_1,
)


def test_follow_path():
    """Test _follow_path utility for extracting values from dict"""
    # Existing path
    val = "foo"
    d = {"a": {"b": [{}, {"c": val}]}}
    assert _follow_path(d, "a", "b", 1, "c") == val

    # Non-existing paths
    d = {"a": {"buzz": val}}
    assert _follow_path(d, "a", "b") is None
    d = {"a": [val]}
    assert _follow_path(d, 1) is None


def test_v0_15_2_to_v0_15_3():
    assert v0_15_2_to_v0_15_3.downgrade(
        v0_15_2_to_v0_15_3.upgrade({"foo": "bar"}).result
    ).result == {"foo": "bar"}

    ct = {"participants": [{"cohort_name": "Not reported"}, {"cohort_name": "foo"}]}

    upgraded_ct = v0_15_2_to_v0_15_3.upgrade(ct).result
    assert upgraded_ct["participants"][0]["cohort_name"] == "Not_reported"
    assert upgraded_ct["participants"][1]["cohort_name"] == "foo"

    assert ct == v0_15_2_to_v0_15_3.downgrade(upgraded_ct).result


def test_v0_10_2_to_v0_11_0():

    empty_ct = {}

    assert v0_10_2_to_v0_11_0.upgrade(empty_ct).result == {
        "allowed_collection_event_names": [],
        "allowed_cohort_names": [],
    }

    ct_2 = {
        "participants": [
            {"cohort_name": "cohort_1"},
            {
                "cohort_name": "cohort_2",
                "samples": [
                    {"collection_event_name": "event_1"},
                    {"collection_event_name": "event_2"},
                ],
            },
        ]
    }

    upgraded = v0_10_2_to_v0_11_0.upgrade(ct_2).result
    assert sorted(upgraded["allowed_collection_event_names"]) == ["event_1", "event_2"]
    assert sorted(upgraded["allowed_cohort_names"]) == ["cohort_1", "cohort_2"]


def test_v0_21_1_to_v0_22_0(monkeypatch):
    monkeypatch.setattr(
        "cidc_schemas.migrations._encrypt", lambda x: f"test_encrypted({str(x)!r})"
    )
    monkeypatch.setattr("cidc_schemas.prism.core._check_encrypt_init", lambda: None)

    empty_ct = {}

    assert v0_21_1_to_v0_22_0.upgrade(empty_ct).result == {}

    ct_2 = {
        "participants": [
            {"participant_id": "pid1", "samples": []},
            {
                "participant_id": "pid2",
                "samples": [
                    {
                        "parent_sample_id": "PARENT_sid_1",
                        "processed_sample_id": "PROCESSED_sid_1",
                    },
                    {"parent_sample_id": "X", "processed_sample_id": "PROCESSED_sid_2"},
                    {
                        "parent_sample_id": "PARENT_sid_3",
                        "processed_sample_id": "test_encrypted('Not reported')",
                    },
                    {
                        "parent_sample_id": "4" * _ENCRYPTED_FIELD_LEN,
                        "processed_sample_id": "4" * _ENCRYPTED_FIELD_LEN,
                    },
                    {"parent_sample_id": "PARENT_sid_5"},
                ],
            },
        ]
    }

    upgraded = v0_21_1_to_v0_22_0.upgrade(ct_2).result
    assert upgraded == {
        "participants": [
            {"participant_id": "test_encrypted('pid1')", "samples": []},
            {
                "participant_id": "test_encrypted('pid2')",
                "samples": [
                    {
                        "parent_sample_id": "test_encrypted('PARENT_sid_1')",
                        "processed_sample_id": "test_encrypted('PROCESSED_sid_1')",
                    },
                    {
                        "parent_sample_id": "test_encrypted('PROCESSED_sid_2')",
                        "processed_sample_id": "test_encrypted('PROCESSED_sid_2')",
                    },
                    {
                        "parent_sample_id": "test_encrypted('PARENT_sid_3')",
                        "processed_sample_id": "test_encrypted('PARENT_sid_3')",
                    },
                    {
                        "parent_sample_id": "4" * _ENCRYPTED_FIELD_LEN,
                        "processed_sample_id": "4" * _ENCRYPTED_FIELD_LEN,
                    },
                    {
                        "parent_sample_id": "test_encrypted('PARENT_sid_5')",
                        "processed_sample_id": "test_encrypted('PARENT_sid_5')",
                    },
                ],
            },
        ]
    }


def test_v0_10_0_to_v0_10_2():

    # Check that upgrade doesn't modify a CT example with no olink data
    ct_no_olink = {"assays": {"wes": {"records": []}}}
    assert v0_10_0_to_v0_10_2.upgrade(ct_no_olink).result == ct_no_olink

    # Check that upgrade throws an error if unexpected olink structure is encountered
    ct_bad_olink = {"assays": {"olink": {"records": [{"files": {}}]}}}
    with pytest.raises(MigrationError, match="Olink record has unexpected structure"):
        v0_10_0_to_v0_10_2.upgrade(ct_bad_olink)

    # Check that the migration treats a well-behaved CT example as expected
    urls = ["tid/olink/chip_1/assay_raw_ct.xlsx", "tid/olink/chip_2/assay_raw_ct.xlsx"]
    old_ct = {
        "assays": {
            "olink": {
                "records": [
                    {
                        "files": {
                            "assay_raw_ct": {
                                "data_format": "XLSX",
                                "object_url": urls[0],
                            }
                        }
                    },
                    {
                        "files": {
                            "assay_raw_ct": {
                                "data_format": "XLSX",
                                "object_url": urls[1],
                            }
                        }
                    },
                ]
            }
        }
    }

    res = v0_10_0_to_v0_10_2.upgrade(old_ct)

    # Extract artifacts from migration result
    get_artifact_path = lambda record_idx: _follow_path(
        res.result, "assays", "olink", "records", record_idx, "files", "assay_raw_ct"
    )

    # Check that artifacts were successfully upgraded and
    # that file_updates track updates as expected
    for i in range(2):
        artifact = get_artifact_path(i)
        assert artifact["data_format"] == "CSV"
        assert artifact["object_url"].endswith(".csv")

        assert urls[i] in res.file_updates
        assert res.file_updates[urls[i]] == artifact

    # Check upgrade/downgrade inverse
    assert v0_10_0_to_v0_10_2.downgrade(res.result).result == old_ct


def test_v0_23_0_to_v0_23_1():
    assert v0_23_0_to_v0_23_1.downgrade(
        v0_23_0_to_v0_23_1.upgrade({"foo": "bar"}).result
    ).result == {"foo": "bar"}

    ct = {
        "participants": [
            {"arbitrary_trial_specific_clinical_annotations": {"foo": "bar"}},
            {"arbitrary_trial_specific_clinical_annotations": {"foo": "baz"}},
        ],
        "analysis": {"rnaseq_analysis": "qux"},
    }

    upgraded_ct = v0_23_0_to_v0_23_1.upgrade(ct).result
    assert (
        "clinical" in upgraded_ct["participants"][0]
        and "arbitrary_trial_specific_clinical_annotations"
        not in upgraded_ct["participants"][0]
    )
    assert (
        "clinical" in upgraded_ct["participants"][1]
        and "arbitrary_trial_specific_clinical_annotations"
        not in upgraded_ct["participants"][1]
    )
    assert (
        "foo" in upgraded_ct["participants"][0]["clinical"]
        and upgraded_ct["participants"][0]["clinical"]["foo"] == "bar"
    )
    assert (
        "foo" in upgraded_ct["participants"][1]["clinical"]
        and upgraded_ct["participants"][1]["clinical"]["foo"] == "baz"
    )
    assert "rnaseq_analysis" not in upgraded_ct["analysis"]
    assert (
        "rna_analysis" in upgraded_ct["analysis"]
        and upgraded_ct["analysis"]["rna_analysis"] == "qux"
    )

    assert ct == v0_23_0_to_v0_23_1.downgrade(upgraded_ct).result
