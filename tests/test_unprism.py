import os
import json
from io import StringIO

import pytest

from cidc_schemas.unprism import (
    _build_artifact,
    derive_files,
    DeriveFilesContext,
    Artifact,
)
from cidc_schemas.prism import PROTOCOL_ID_FIELD_NAME, SUPPORTED_SHIPPING_MANIFESTS

ct_example_path = os.path.join(
    os.path.dirname(__file__), "data/clinicaltrial_examples/CT_1.json"
)


@pytest.fixture
def ct():
    with open(ct_example_path, "r") as ct:
        yield json.load(ct)


def test_build_artifact():
    """Check that the artifact building helper works as expected"""
    trial_id = "test-trial"
    trial_metadata = {PROTOCOL_ID_FIELD_NAME: trial_id}
    upload_type = "bar"

    context = DeriveFilesContext(trial_metadata, upload_type, None)

    name = "foo.txt"
    data = "blahblah"
    typ = "pbmc"
    fmt = "csv"

    # without extra metadata
    assert _build_artifact(context, name, data, typ, fmt) == Artifact(
        f"{trial_id}/{name}", data, typ, fmt, None
    )
    assert _build_artifact(
        context, "foo.txt", data, typ, fmt, include_upload_type=True
    ) == Artifact(f"{trial_id}/{upload_type}/{name}", data, typ, fmt, None)

    # with extra metadata
    metadata = {1: 2}
    assert _build_artifact(context, name, data, typ, fmt, metadata) == Artifact(
        f"{trial_id}/{name}", data, typ, fmt, metadata
    )


@pytest.mark.parametrize("upload_type", SUPPORTED_SHIPPING_MANIFESTS)
def test_derive_files_shipping_manifest(ct, upload_type):
    """Check that participants and samples CSVs are derived as expected."""
    result = derive_files(DeriveFilesContext(ct, upload_type, None))
    assert result.artifacts == [
        Artifact(
            "10021/participants.csv",
            "participants info",
            "csv",
            (
                f"cimac_participant_id,participant_id,cohort_name,{PROTOCOL_ID_FIELD_NAME}\n"
                "CTTTPP1,trial.PA.1,Arm_Z,10021\n"
                "CTTTPP2,trial.PA.2,Arm_Z,10021\n"
            ),
            None,
        ),
        Artifact(
            "10021/samples.csv",
            "samples info",
            "csv",
            (
                f"cimac_id,parent_sample_id,collection_event_name,sample_location,type_of_sample,type_of_primary_container,{PROTOCOL_ID_FIELD_NAME},participants.cimac_participant_id\n"
                "CTTTPP1S1.00,SA.1.1,Baseline,---,Other,Other,10021,CTTTPP1\n"
                "CTTTPP1S2.00,SA.1.2,Baseline,---,Other,Other,10021,CTTTPP1\n"
                "CTTTPP2S1.00,SA.2.1,Baseline,---,Other,Other,10021,CTTTPP2\n"
                "CTTTPP2S2.00,SA.2.2,Baseline,---,Other,Other,10021,CTTTPP2\n"
            ),
            None,
        ),
    ]
