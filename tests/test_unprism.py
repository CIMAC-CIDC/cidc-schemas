import os
import json

import pytest

from cidc_schemas.unprism import unprism_participants, unprism_samples
from cidc_schemas.prism import PROTOCOL_ID_FIELD_NAME

ct_example_path = os.path.join(os.path.dirname(
    __file__), 'data/clinicaltrial_examples/CT_1.json')


@pytest.fixture
def ct():
    with open(ct_example_path, 'r') as ct:
        yield json.load(ct)


def test_unprism_participants(ct):
    """Check that we can extract patient-level data from a trial metadata object."""
    csv = unprism_participants(ct)

    expected = (
        f"cimac_participant_id,participant_id,cohort_name,{PROTOCOL_ID_FIELD_NAME}\n"
        "CM-TEST-PAR1,trial.PA.1,Arm_Z,10021\n"
        "CM-TEST-PAR2,trial.PA.2,Arm_Z,10021\n"
    )

    assert csv == expected


def test_unprism_samples(ct):
    """Check that we can extract sample-level data from a trial metadata object."""
    csv = unprism_samples(ct)

    expected = (
        f"cimac_id,parent_sample_id,collection_event_name,sample_location,type_of_sample,type_of_primary_container,{PROTOCOL_ID_FIELD_NAME},participants.cimac_participant_id\n"
        "CM-TEST-PAR1-S1,SA.1.1,Baseline,---,Other,Other,10021,CM-TEST-PAR1\n"
        "CM-TEST-PAR1-S2,SA.1.2,Baseline,---,Other,Other,10021,CM-TEST-PAR1\n"
        "CM-TEST-PAR2-S1,SA.2.1,Baseline,---,Other,Other,10021,CM-TEST-PAR2\n"
        "CM-TEST-PAR2-S2,SA.2.2,Baseline,---,Other,Other,10021,CM-TEST-PAR2\n"
    )

    assert csv == expected
