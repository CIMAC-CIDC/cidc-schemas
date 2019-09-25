from cidc_schemas.unprism import unprism_participants, unprism_samples
from cidc_schemas.json_validation import load_and_validate_schema


def _validate_ct(ct: dict):
    validator = load_and_validate_schema(
        'clinical_trial.json', return_validator=True)
    validator.validate(ct)


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
                "cimac_participant_id": "CM-TEST-PA11",
                "trial_participant_id": "tPA1"
            },
            {
                "race": "White",
                "gender": "Other",
                "arm_id": "12345",
                "samples": [],
                "cohort_id": "54321",
                "cimac_participant_id": "CM-TEST-PA12",
                "trial_participant_id": "tPA2"
            }
        ],
    }

    # Validate the trial_metadata object to ensure this test fails
    # if the data model changes.
    _validate_ct(trial_metadata)

    csv = unprism_participants(trial_metadata)
    expected = """,arm_id,gender,cohort_id,cimac_participant_id,trial_participant_id,race,lead_organization_study_id
0,12345,Male,54321,CM-TEST-PA11,tPA1,,test_trial_id
1,12345,Other,54321,CM-TEST-PA12,tPA2,White,test_trial_id
"""
    assert csv == expected


def test_unprism_samples():
    """
    Check that we can extract sample-level data from a trial metadata object with multiple
    participants and different properties in different samples.
    """

    extra_participant_fields = {
        "trial_participant_id": "",
        "cohort_id": "",
        "arm_id": "",
    }

    trial_metadata = {
        "lead_organization_study_id": "1/minimal",
        "participants": [
            {
                "cimac_participant_id": "CM-TEST-PA11",
                **extra_participant_fields,
                "samples": [
                    {
                        "cimac_id": "CM-TEST-PA11-S1",
                        "site_sample_id": "site.SA.1.1.1",
                        "time_point": "---",
                        "sample_location": "---",
                        "specimen_type": "Other",
                        "specimen_format": "Other",
                        "genomic_source": "Normal",
                        "aliquots": []
                    },
                    {
                        "cimac_id": "CM-TEST-PA11-S2",
                        "site_sample_id": "site.SA.1.1.2",
                        "time_point": "---",
                        "sample_location": "---",
                        "specimen_format": "FFPE Block",
                        "specimen_type": "Plasma",
                        "genomic_source": "Tumor",
                        "aliquots": []
                    }
                ]
            },
            {
                "cimac_participant_id": "CM-TEST-PA12",
                **extra_participant_fields,
                "samples": [
                    {
                        "cimac_id": "CM-TEST-PA12-S1",
                        "site_sample_id": "site.SA.1.2.1",
                        "time_point": "---",
                        "sample_location": "---",
                        "specimen_type": "Other",
                        "specimen_format": "EDTA Tube",
                        "genomic_source": "Normal",
                        "aliquots": []
                    },
                    {
                        "cimac_id": "CM-TEST-PA12-S2",
                        "site_sample_id": "site.SA.1.2.2",
                        "time_point": "---",
                        "sample_location": "---",
                        "specimen_type": "PBMC",
                        "specimen_format": "EDTA Tube",
                        "genomic_source": "Tumor",
                        "aliquots": []
                    }
                ]
            }
        ]
    }

    # Validate the trial_metadata object to ensure this test fails
    # if the data model changes.
    _validate_ct(trial_metadata)

    csv = unprism_samples(trial_metadata)

    expected = """,cimac_id,site_sample_id,time_point,sample_location,specimen_type,specimen_format,genomic_source,lead_organization_study_id,participants.cimac_participant_id
0,CM-TEST-PA11-S1,site.SA.1.1.1,---,---,Other,Other,Normal,1/minimal,CM-TEST-PA11
1,CM-TEST-PA11-S2,site.SA.1.1.2,---,---,Plasma,FFPE Block,Tumor,1/minimal,CM-TEST-PA11
2,CM-TEST-PA12-S1,site.SA.1.2.1,---,---,Other,EDTA Tube,Normal,1/minimal,CM-TEST-PA12
3,CM-TEST-PA12-S2,site.SA.1.2.2,---,---,PBMC,EDTA Tube,Tumor,1/minimal,CM-TEST-PA12
"""

    assert csv == expected
