import pytest

from cidc_schemas.prism.patch_feedback import manifest_feedback


TEST_SET = []

TEST_SET.append(
    (
        {
            "protocol_identifier": "trial",
            "shipments": [{"manifest_id": "manifest", "assay_type": "assay"}],
            "participants": [
                {
                    "cimac_participant_id": "C_____1",
                    "samples": [
                        {
                            "cimac_id": "C_____1_1.01",
                            "parent_sample_id": "parent_1",
                            "processed_sample_id": "processed_1",
                            "collection_event_name": "time_point_1",
                        }
                    ],
                }
            ],
        },
        {},
        [
            "1 samples from 1 participants in manifest 'manifest' for trial/assay",
            [
                "adds 1 new participants",
                [
                    "with 1 new sample: 1 sample per participant",
                    "collection_event_name event for all 1 - time_point_1",
                ],
            ],
        ],
    )
)


TEST_SET.append(
    (
        {
            "protocol_identifier": "trial",
            "shipments": [{"manifest_id": "manifest", "assay_type": "assay"}],
            "participants": [
                {
                    "cimac_participant_id": "C_____1",
                    "samples": [
                        {
                            "cimac_id": "C_____1_1.01",
                            "parent_sample_id": "parent_1",
                            "processed_sample_id": "processed_1",
                            "collection_event_name": "time_point_1",
                        }
                    ],
                }
            ],
        },
        {
            "participants": [
                {
                    "cimac_participant_id": "C_____1",
                    "samples": [
                        {
                            "cimac_id": "C_____1_0.01",
                            "parent_sample_id": "parent_1",
                            "processed_sample_id": "processed_1",
                            "collection_event_name": "time_point_1",
                        }
                    ],
                }
            ]
        },
        [
            "1 samples from 1 participants in manifest 'manifest' for trial/assay",
            ["adds 0 new participants"],
            [
                "updates 1 existing participants",
                [
                    "with 1 new sample: 1 sample per participant",
                    "collection_event_name event for all 1 - time_point_1",
                ],
            ],
        ],
    )
)


TEST_SET.append(
    (
        {
            "protocol_identifier": "trial",
            "shipments": [{"manifest_id": "manifest", "assay_type": "assay"}],
            "participants": [
                {
                    "cimac_participant_id": "C_____2",
                    "samples": [
                        {
                            "cimac_id": "C_____2_1.01",
                            "parent_sample_id": "parent_1",
                            "processed_sample_id": "processed_1",
                            "collection_event_name": "time_point_1",
                        },
                        {
                            "cimac_id": "C_____2_2.01",
                            "parent_sample_id": "parent_1",
                            "processed_sample_id": "processed_1",
                            "collection_event_name": "time_point_2",
                        },
                    ],
                }
            ],
        },
        {},
        [
            "2 samples from 1 participants in manifest 'manifest' for trial/assay",
            [
                "adds 1 new participants",
                [
                    "with 2 new samples: 2 samples per participant",
                    "Found the same parent_sample_id 'parent_1' for all 2 samples",
                    "Found the same processed_sample_id 'processed_1' for all 2 samples",
                    "2 collection events",
                    ["1 time_point_1's", "1 time_point_2's"],
                ],
            ],
        ],
    )
)


@pytest.mark.parametrize("patch,current_md,expected", TEST_SET)
def test_manifest_feedback(patch, current_md, expected):
    """Check that the manifest_feedback the expected output on a friendly input"""

    result = manifest_feedback("plasma", patch, current_md)
    assert expected == result


def test_unsupported_manifest_feedback():
    """Check that the manifest_feedback doesn't fail on unsupported"""

    assert [] == manifest_feedback("very_unsupoorted_type", {"something": "cool"}, {})
