"""Tests for pipeline config generation."""
from cidc_schemas.prism.merger import ArtifactInfo
import os
import copy
import yaml
import csv

import pytest

from cidc_schemas.template import Template, _TEMPLATE_PATH_MAP
from cidc_schemas.template_reader import XlTemplateReader
from cidc_schemas.prism import core, pipelines, merger

from ..constants import TEMPLATE_EXAMPLES_DIR
from ..test_templates import (
    template_set,
    template,
    template_example,
    template_example_xlsx_path,
)
from .cidc_test_data import get_test_trial


@pytest.fixture(scope="session")
def prismify_result(template, template_example):

    # tear down
    core._encrypt_hmac = None
    # and set up
    core.set_prism_encrypt_key("test")

    prism_patch, file_maps, errs = core.prismify(template_example, template)
    assert not errs, "\n".join([str(e) for e in errs])
    return prism_patch, file_maps, errs


def prism_patch_stage_artifacts(prismify_result, template_type):

    prism_patch, prism_fmap, _ = prismify_result
    patch_copy_4_artifacts = copy.deepcopy(prism_patch)

    patch_copy_4_artifacts = merger.merge_artifacts(
        patch_copy_4_artifacts,
        [
            merger.ArtifactInfo(
                artifact_uuid=fmap_entry.upload_placeholder,
                object_url=fmap_entry.gs_key,
                upload_type=template_type,
                file_size_bytes=i,
                uploaded_timestamp="01/01/2001",
                md5_hash=f"hash_{i}",
            )
            for i, fmap_entry in enumerate(prism_fmap)
        ],
    )[0]

    return patch_copy_4_artifacts


def stage_assay_for_analysis(template_type):
    """
    Simulates an initial assay upload by prismifying the initial assay template object.
    """

    staging_map = {
        "cytof_analysis": "cytof",
        "tumor_normal_pairing": "wes_fastq",
    }

    if not template_type in staging_map:
        return {}

    prelim_assay = staging_map[template_type]

    preassay_xlsx_path = os.path.join(
        TEMPLATE_EXAMPLES_DIR, prelim_assay + "_template.xlsx"
    )
    preassay_xlsx, _ = XlTemplateReader.from_excel(preassay_xlsx_path)
    preassay_template = Template.from_type(prelim_assay)
    prism_res = core.prismify(preassay_xlsx, preassay_template)

    return prism_patch_stage_artifacts(prism_res, prelim_assay)


def test_WES_pipeline_config_generation_after_prismify(prismify_result, template):

    if not (template.type.startswith("wes_") or "pair" in template.type):
        return

    # Test that the config generator blocks disallowed upload types
    upload_type = "foo"
    with pytest.raises(NotImplementedError, match=f"Not supported type:{upload_type}"):
        pipelines._Wes_pipeline_config(upload_type)

    full_ct = get_test_trial(
        [
            "CTTTPP111.00",
            "CTTTPP121.00",
            "CTTTPP122.00",
            "CTTTPP121.00",
            "CTTTPP123.00",
        ],
        assays={"wes": []},
    )

    patch_with_artifacts = prism_patch_stage_artifacts(prismify_result, template.type)

    # if it's an analysis - we need to merge corresponding preliminary assay first
    prelim_assay = stage_assay_for_analysis(template.type)
    if prelim_assay:
        full_ct, errs = merger.merge_clinical_trial_metadata(prelim_assay, full_ct)
        assert 0 == len(errs), str(errs)

    full_ct, errs = merger.merge_clinical_trial_metadata(patch_with_artifacts, full_ct)
    assert 0 == len(errs), str(errs)

    res = pipelines.generate_analysis_configs_from_upload_patch(
        full_ct, patch_with_artifacts, template.type, "my-biofx-bucket"
    )

    # where we don't expect to have configs
    if not template.type in pipelines._ANALYSIS_CONF_GENERATORS:
        assert res == {}
        return

    elif "pair" in template.type:
        # only returns tumor/normal
        assert len(res) == 1
    else:
        # in other cases - 2 config, tumor/normal and tumor-only
        assert len(res) == 2

    for fname, conf in res.items():
        conf = yaml.load(conf, Loader=yaml.FullLoader)
        print(conf)

        assert len(conf["metasheet"]) == 1  # one run

        if "pair" in template.type:
            assert len(conf["samples"]) in [1, 2]
            assert conf["instance_name"] == (
                "ctttpp111-00"  # run_id from sheet
                if len(conf["samples"]) == 2  # tumor/normal
                else "ctttpp122-00"  # tumor id for tumor-only
            )  # run ID but lowercase & hyphenated

        else:
            assert len(conf["samples"]) == 1  # tumor only
            assert conf["instance_name"] in [
                "ctttpp111-00",
                "ctttpp121-00",
            ]  # CIMAC ID but lowercase & hypenated

        for sample in conf["samples"].values():
            assert len(sample) > 0  # at lease one data file per sample
            assert all("my-biofx-bucket" in f for f in sample)
            assert all(f.endswith(".fastq.gz") for f in sample) or all(
                f.endswith(".bam") for f in sample
            )


def test_RNAseq_pipeline_config_generation_after_prismify(prismify_result, template):

    if not template.type.startswith("rna_"):
        return

    full_ct = get_test_trial(
        ["CTTTPP111.00", "CTTTPP121.00", "CTTTPP122.00", "CTTTPP123.00"],
        assays={"rna": []},
    )
    patch_with_artifacts = prism_patch_stage_artifacts(prismify_result, template.type)

    # if it's an analysis - we need to merge corresponding preliminary assay first
    prelim_assay = stage_assay_for_analysis(template.type)
    if prelim_assay:
        full_ct, errs = merger.merge_clinical_trial_metadata(prelim_assay, full_ct)
        assert 0 == len(errs)

    full_ct, errs = merger.merge_clinical_trial_metadata(patch_with_artifacts, full_ct)

    assert 0 == len(errs), "\n".join(errs)

    res = pipelines.generate_analysis_configs_from_upload_patch(
        full_ct, patch_with_artifacts, template.type, "my-biofx-bucket"
    )

    # where we don't expect to have configs
    if not template.type in pipelines._ANALYSIS_CONF_GENERATORS:
        assert res == {}
        return

    if template.type in ["rna_fastq", "rna_bam"]:
        # one config with all samples from one participant in one example .xlsx
        # plus one metasheet.csv
        assert len(res) == 1 + 1

    else:
        assert False, f"Unexpected RNAseq template test {template.type}"

    for fname, fcontent in res.items():

        if not fname.endswith(".yaml"):
            assert fname.endswith(".csv")

            assert (
                fcontent
                == "cimac_id,cimac_participant_id,collection_event_name,type_of_sample,processed_sample_derivative"
                "\r\nCTTTPP122.00,CTTTPP1,Not_reported,Not Reported,"
                "\r\nCTTTPP123.00,CTTTPP1,Not_reported,Not Reported,"
            )

        else:

            conf = yaml.load(fcontent, Loader=yaml.FullLoader)

            assert len(conf["runs"]) == 2  # two runs for two samples in example .xlsx

            assert len(conf["samples"]) == 2  # two samples in example .xlsx
            for sample in conf["samples"].values():
                assert len(sample) > 0  # at lease one data file per sample
                assert all("my-biofx-bucket" in f for f in sample)
                assert all(f.endswith(".fastq.gz") for f in sample) or all(
                    f.endswith(".bam") for f in sample
                )
