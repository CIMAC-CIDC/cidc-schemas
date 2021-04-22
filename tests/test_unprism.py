import os
import json
from io import BytesIO, StringIO
import csv
import pandas as pd

import pytest

from cidc_schemas.unprism import (
    _build_artifact,
    derive_files,
    DeriveFilesContext,
    Artifact,
)
from cidc_schemas.prism import PROTOCOL_ID_FIELD_NAME, SUPPORTED_SHIPPING_MANIFESTS
from cidc_schemas.util import participant_id_from_cimac

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


@pytest.mark.parametrize("upload_type", SUPPORTED_SHIPPING_MANIFESTS, ids=lambda x: x)
def test_derive_files_shipping_manifest(ct, upload_type):
    """Check that participants and samples CSVs are derived as expected."""
    result = derive_files(DeriveFilesContext(ct, upload_type, None))
    assert result.artifacts == [
        Artifact(
            object_url="10021/participants.csv",
            file_type="participants info",
            data_format="csv",
            data=(
                f"cimac_participant_id,cidc_participant_id,participant_id,cohort_name,{PROTOCOL_ID_FIELD_NAME}\n"
                "CTTTPP1,CIDC-10021-pPpPp1,trial.PA.1,Arm_Z,10021\n"
                "CTTTPP2,CIDC-10021-pPpPp2,trial.PA.2,Arm_Z,10021\n"
            ),
            metadata=None,
        ),
        Artifact(
            object_url="10021/samples.csv",
            file_type="samples info",
            data_format="csv",
            data=(
                f"cimac_id,cidc_id,parent_sample_id,collection_event_name,sample_location,type_of_sample,type_of_primary_container,sample_volume_units,material_used,material_remaining,quality_of_sample,{PROTOCOL_ID_FIELD_NAME},participants.cimac_participant_id\n"
                "CTTTPP1S1.00,CIDC-10021-pPpPp1-sS0,SA.1.1,Baseline,---,Other,Other,Other,1,0,Other,10021,CTTTPP1\n"
                "CTTTPP1S1.01,CIDC-10021-pPpPp1-sS1,SA.1.1,Baseline,---,Other,Other,Other,1,0,Other,10021,CTTTPP1\n"
                "CTTTPP1S2.00,CIDC-10021-pPpPp1-sS2,SA.1.2,Baseline,---,Other,Other,Other,1,0,Other,10021,CTTTPP1\n"
                "CTTTPP2S1.00,CIDC-10021-pPpPp2-sS0,SA.2.1,Baseline,---,Other,Other,Other,1,0,Other,10021,CTTTPP2\n"
                "CTTTPP2S1.01,CIDC-10021-pPpPp2-sS1,SA.2.1,Baseline,---,Other,Other,Other,1,0,Other,10021,CTTTPP2\n"
                "CTTTPP2S2.00,CIDC-10021-pPpPp2-sS2,SA.2.2,Baseline,---,Other,Other,Other,1,0,Other,10021,CTTTPP2\n"
                "CTTTPP2S2.01,CIDC-10021-pPpPp2-sS3,SA.2.2,Baseline,---,Other,Other,Other,1,0,Other,10021,CTTTPP2\n"
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


def test_derive_files_olink():
    partial_ct = {
        PROTOCOL_ID_FIELD_NAME: "test-trial",
        "assays": {
            "olink": {
                "study": {"npx_file": {"object_url": "foo"}},
                "batches": [
                    {
                        "combined": {"npx_file": {"object_url": "bar"}},
                        "records": [{"files": {"assay_npx": {"object_url": "baz"}}}],
                    }
                ],
            }
        },
    }

    header = "CIMAC_10021_IO,Olink NPX Manager 2.0.1.175,\nNPX data,,\nPanel,Olink IMMUNO-ONCOLOGY(v.3111),Olink IMMUNO-ONCOLOGY(v.3111)\n"
    columns = "Assay,IL8,Inc Ctrl 1\nUniprot ID,P10145,-\nOlinkID,OID00752,\n\n"  # missing space in 'OlinkID' to mimic received data
    columns_space = "Assay,IL8,Inc Ctrl 1\nUniprot ID,P10145,-\nOlink ID,OID00752,\n\n"  # with space follows standard
    columns_after = "Assay,IL8\nUniprot ID,P10145\nOlink ID,OID00752\nLOD,1.15432\n"
    non_cimac = "NC1,-0.64245,-0.06713\n"
    cimac1 = "CNNNNNNNN.01,8.14109,0\n"
    cimac1_after = "CNNNNNNNN.01,8.14109\n"
    cimac2 = "CMMMMMMMM.01,6.63796,0\n"
    cimac2_after = "CMMMMMMMM.01,6.63796\n"
    footer = "\nLOD,1.15432,0.47603\nMissing Data freq.,0.05,0.07\n"

    def fetch_artifact(url: str, as_string: bool) -> StringIO:
        assert url in ("foo", "bar", "baz")
        if url == "foo":
            df = pd.read_csv(StringIO(header + columns + cimac1 + cimac2 + footer))
        elif url == "bar":
            df = pd.read_csv(
                StringIO(header + columns_space + non_cimac + cimac1 + footer)
            )
        else:
            df = pd.read_csv(
                StringIO(header + columns + non_cimac + cimac1 + cimac2 + footer)
            )

        buff = BytesIO()
        with pd.ExcelWriter(buff) as writer:
            df.to_excel(writer, sheet_name="NPX Data", index=False)
        return buff

    result = derive_files(DeriveFilesContext(partial_ct, "olink", fetch_artifact))
    assert len(result.artifacts) == 1
    assert result.artifacts[0].data == (columns_after + cimac1_after + cimac2_after)

    del partial_ct["assays"]["olink"]["study"]
    result = derive_files(DeriveFilesContext(partial_ct, "olink", fetch_artifact))
    assert len(result.artifacts) == 1
    assert result.artifacts[0].data == (columns_after + cimac1_after)

    del partial_ct["assays"]["olink"]["batches"][0]["combined"]
    result = derive_files(DeriveFilesContext(partial_ct, "olink", fetch_artifact))
    assert len(result.artifacts) == 1
    assert result.artifacts[0].data == (columns_after + cimac1_after + cimac2_after)


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


def load_ct_example(name: str) -> dict:
    with open(
        os.path.join(
            os.path.dirname(__file__), f"data/clinicaltrial_examples/{name}.json"
        ),
        "r",
    ) as f:
        return json.load(f)


def test_derive_files_CyTOF_analysis():
    """Check that CyTOF analysis CSV is derived as expected."""

    ct = load_ct_example("CT_cytof_10021_with_analysis")

    artifact_format_specific_data = {
        "cell_counts_assignment": {"B Cell (CD27-)": 272727, "B Cell (Memory)": 11111},
        "cell_counts_compartment": {"B Cell": 8888, "Granulocyte": 22222},
        "cell_counts_profiling": {
            "B Cell (CD27-) CD1chi CD38hi": "138hi",
            "B Cell (CD27-) CD1chi CD38lo": "138lo",
        },
    }

    def fetch_artifact(url: str, as_string: bool) -> StringIO:
        for (ftype, data) in artifact_format_specific_data.items():
            if ftype in url:
                csv = '"","CellSubset","N"\n'
                csv += "\n".join(
                    f'"{i}","{k}",{v}' for i, (k, v) in enumerate(data.items())
                )

                return StringIO(csv)
        raise Exception(f"Unknown file for url {url}")

    result = derive_files(DeriveFilesContext(ct, "cytof_analysis", fetch_artifact))
    assert len(result.artifacts) == 3

    artifacts = {a.file_type.replace(" ", "_"): a for a in result.artifacts}
    # checking that there are 1 file per `file_type`
    assert len(artifacts) == 3

    for ar_format, artifact in artifacts.items():
        format_specific_truth = artifact_format_specific_data[ar_format]
        req_header_fields = list(format_specific_truth.keys())

        cimac_ids = sorted(["CTSTP01S2.01", "CTSTP01S1.01"])

        dictreader = csv.DictReader(StringIO(artifact.data))

        recs = []
        for row in dictreader:
            recs.append(row)
            rec = ",".join(row[f] for f in req_header_fields)
            should_be = ",".join(
                str(format_specific_truth[f]) for f in req_header_fields
            )
            assert rec == should_be
        assert sorted([r["cimac_id"] for r in recs]) == cimac_ids
        assert sorted([r["cimac_participant_id"] for r in recs]) == sorted(
            list(map(participant_id_from_cimac, cimac_ids))
        )
