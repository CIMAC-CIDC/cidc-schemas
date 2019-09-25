from cidc_schemas.unprism import unprism_participants, unprism_samples


def test_unprism_participants():
    """Check that we can extract patient-level data from a trial metadata object."""
    trial_metadata = {
        "lead_organization_study_id": "test_trial_id",
        "participants": [
            {
                "arm_id": "12345",
                "gender": "Male",
                "samples": [],
                "cohort_id": "54321",
                "cimac_participant_id": "PA1",
                "trial_participant_id": "tPA1"
            },
            {
                "race": "White",
                "gender": "Other",
                "arm_id": "12345",
                "samples": [],
                "cohort_id": "54321",
                "cimac_participant_id": "PA2",
                "trial_participant_id": "tPA2"
            }
        ],
    }

    csv = unprism_participants(trial_metadata)
    expected = """,arm_id,gender,cohort_id,cimac_participant_id,trial_participant_id,race,lead_organization_study_id
        0,12345,Male,54321,PA1,tPA1,,test_trial_id
        1,12345,Other,54321,PA2,tPA2,White,test_trial_id
    """.replace(" ", "")
    assert csv == expected


def test_unprism_samples():
    """
    Check that we can extract sample-level data from a trial metadata object with multiple
    participants and different properties in different samples.
    """
    trial_metadata = {
        "lead_organization_study_id": "1/minimal",
        "participants": [
            {
                "cimac_participant_id": "PA.1.1",
                "samples": [
                    {
                        "cimac_id": "SA.1.1.1",
                        "site_sample_id": "site.SA.1.1.1",
                        "time_point": "---",
                        "sample_location": "---",
                        "specimen_type": "Other",
                        "specimen_format": "Other",
                        "genomic_source": "Normal",
                        "aliquots": []
                    },
                    {
                        "cimac_id": "SA.1.1.2",
                        "site_sample_id": "site.SA.1.1.2",
                        "time_point": "---",
                        "specimen_type": "plasma",
                        "aliquots": []
                    }
                ]
            },
            {
                "cimac_participant_id": "PA.1.2",
                "samples": [
                    {
                        "cimac_id": "SA.1.2.1",
                        "site_sample_id": "site.SA.1.2.1",
                        "time_point": "---",
                        "sample_location": "---",
                        "specimen_type": "Other",
                        "specimen_format": "Other",
                        "genomic_source": "Normal",
                        "aliquots": []
                    },
                    {
                        "cimac_id": "SA.1.2.2",
                        "site_sample_id": "site.SA.1.2.2",
                        "time_point": "---",
                        "specimen_type": "pbmc",
                        "aliquots": []
                    }
                ]
            }
        ]
    }

    csv = unprism_samples(trial_metadata)

    expected = """,cimac_id,site_sample_id,time_point,sample_location,specimen_type,specimen_format,genomic_source,lead_organization_study_id,participants.cimac_participant_id
        0,SA.1.1.1,site.SA.1.1.1,---,---,Other,Other,Normal,1/minimal,PA.1.1
        1,SA.1.1.2,site.SA.1.1.2,---,,plasma,,,1/minimal,PA.1.1
        2,SA.1.2.1,site.SA.1.2.1,---,---,Other,Other,Normal,1/minimal,PA.1.2
        3,SA.1.2.2,site.SA.1.2.2,---,,pbmc,,,1/minimal,PA.1.2
    """.replace(" ", "")

    assert csv == expected
