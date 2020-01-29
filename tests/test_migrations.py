import pytest

from cidc_schemas.migrations import (
    _follow_path,
    v0_10_0_to_v0_10_2,
    MigrationError,
    v0_10_2_to_v0_11_0,
    v0_15_2_to_v0_15_3,
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
