import os
import json
from io import StringIO

import pytest

from cidc_schemas.unprism import ShippingManifestDerivation, DeriveFilesContext
from cidc_schemas.prism import PROTOCOL_ID_FIELD_NAME

ct_example_path = os.path.join(
    os.path.dirname(__file__), "data/clinicaltrial_examples/CT_1.json"
)


@pytest.fixture
def ct():
    with open(ct_example_path, "r") as ct:
        yield json.load(ct)


def test_shipping_manifest_derivation(ct):
    """Check that participants and samples CSVs are derived as expected."""

    def fake_save_artifact(url: str, csv: StringIO):
        if url == "10021/participants.csv":
            assert csv.read() == (
                f"cimac_participant_id,participant_id,cohort_name,{PROTOCOL_ID_FIELD_NAME}\n"
                "CTTTPP1,trial.PA.1,Arm_Z,10021\n"
                "CTTTPP2,trial.PA.2,Arm_Z,10021\n"
            )
        elif url == "10021/samples.csv":
            assert csv.read() == (
                f"cimac_id,parent_sample_id,collection_event_name,sample_location,type_of_sample,type_of_primary_container,{PROTOCOL_ID_FIELD_NAME},participants.cimac_participant_id\n"
                "CTTTPP1S1.00,SA.1.1,Baseline,---,Other,Other,10021,CTTTPP1\n"
                "CTTTPP1S2.00,SA.1.2,Baseline,---,Other,Other,10021,CTTTPP1\n"
                "CTTTPP2S1.00,SA.2.1,Baseline,---,Other,Other,10021,CTTTPP2\n"
                "CTTTPP2S2.00,SA.2.2,Baseline,---,Other,Other,10021,CTTTPP2\n"
            )
        else:
            assert 0, f"Unexpected participants/samples CSV url: {url}"

    derivation = ShippingManifestDerivation()
    derivation(
        ct, DeriveFilesContext(fetch_artifact=None, save_artifact=fake_save_artifact)
    )
