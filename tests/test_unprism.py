import os
import json
from io import StringIO
import csv

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
            object_url="10021/participants.csv",
            file_type="participants info",
            data_format="csv",
            data=(
                f"cimac_participant_id,participant_id,cohort_name,{PROTOCOL_ID_FIELD_NAME}\n"
                "CTTTPP1,trial.PA.1,Arm_Z,10021\n"
                "CTTTPP2,trial.PA.2,Arm_Z,10021\n"
            ),
            metadata=None,
        ),
        Artifact(
            object_url="10021/samples.csv",
            file_type="samples info",
            data_format="csv",
            data=(
                f"cimac_id,parent_sample_id,collection_event_name,sample_location,type_of_sample,type_of_primary_container,{PROTOCOL_ID_FIELD_NAME},participants.cimac_participant_id\n"
                "CTTTPP1S1.00,SA.1.1,Baseline,---,Other,Other,10021,CTTTPP1\n"
                "CTTTPP1S2.00,SA.1.2,Baseline,---,Other,Other,10021,CTTTPP1\n"
                "CTTTPP2S1.00,SA.2.1,Baseline,---,Other,Other,10021,CTTTPP2\n"
                "CTTTPP2S2.00,SA.2.2,Baseline,---,Other,Other,10021,CTTTPP2\n"
            ),
            metadata=None,
        ),
    ]


def test_derive_files_IHC():
    """Check that IHC CSV is derived as expected."""

    with open(
        os.path.join(
            os.path.dirname(__file__), "data/clinicaltrial_examples/CT_ihc.json"
        ),
        "r",
    ) as f:
        ct = json.load(f)

    result = derive_files(DeriveFilesContext(ct, "ihc", None))
    assert len(result.artifacts) == 1

    req_header_fields = [
        "marker_positive",
        "tumor_proportion_score",
        PROTOCOL_ID_FIELD_NAME,
    ]

    true_recs = {
        "CTTTPP1S1.00": "positive,0.0,test_example_ihc",
        "CTTTPP2S1.00": "negative,0.0,test_example_ihc",
        "CTTTPP2S2.00": "no_call,0.0,test_example_ihc",
    }

    dictreader = csv.DictReader(StringIO(result.artifacts[0].data))

    recs = {}
    for row in dictreader:
        cimac_id = row["cimac_id"]
        rec = ",".join(row[f] for f in req_header_fields)
        recs[cimac_id] = rec

    assert recs == true_recs


def test_derive_files_wes_analysis():
    """Check that combined MAF is derived as expected"""
    url1 = "a"
    url2 = "b"
    trial_id = "test-trial"
    partial_ct = {
        PROTOCOL_ID_FIELD_NAME: trial_id,
        "analysis": {
            "wes_analysis": {
                "pair_runs": [
                    {"somatic": {"maf_tnscope_filter": {"object_url": url1}}},
                    {"somatic": {"maf_tnscope_filter": {"object_url": url2}}},
                ]
            }
        },
    }

    version = "#version 1.0\n"
    headers = "col1\tcol2\tcol3\n"
    maf1 = "a\tb\tc\n" "d\t\tf\n"
    maf2 = "c\tb\t\n" "f\te\td\n"

    def fetch_artifact(url: str, as_string: bool) -> StringIO:
        assert url in (url1, url2)
        if url == url1:
            return StringIO(version + headers + maf1)
        else:
            return StringIO(version + headers + maf2)

    context = DeriveFilesContext(partial_ct, "wes_analysis", fetch_artifact)
    result = derive_files(context)

    assert result.trial_metadata == partial_ct
    assert len(result.artifacts) == 1

    combined_maf = result.artifacts[0]

    assert combined_maf.data_format == "maf"
    assert combined_maf.file_type == "combined maf"
    assert combined_maf.data == headers + maf1 + maf2
