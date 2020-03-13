"""Tests for CIDC data model-specific prism functionality."""

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for PRISM the module which pulls JSON objects from excel spreadsheets."""

import os
import copy
import pytest
import jsonschema
import json
import yaml
from deepdiff import grep, DeepDiff
from collections import namedtuple
from jsonmerge import Merger
from unittest.mock import MagicMock, patch as mock_patch


from cidc_schemas import prism
from cidc_schemas.prism import core, merger as prism_merger, pipelines
from cidc_schemas.prism import (
    prismify,
    merge_artifact,
    merge_clinical_trial_metadata,
    InvalidMergeTargetException,
    SUPPORTED_ASSAYS,
    SUPPORTED_SHIPPING_MANIFESTS,
    SUPPORTED_MANIFESTS,
    SUPPORTED_TEMPLATES,
    SUPPORTED_ANALYSES,
    PROTOCOL_ID_FIELD_NAME,
    parse_npx,
    parse_elisa,
    merge_artifact_extra_metadata,
    MergeCollisionException,
    generate_analysis_configs_from_upload_patch,
)

from cidc_schemas.json_validation import load_and_validate_schema, InDocRefNotFoundError
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.util import participant_id_from_cimac
from cidc_schemas.template_reader import XlTemplateReader

from ..constants import (
    TEST_DATA_DIR,
    ROOT_DIR,
    SCHEMA_DIR,
    TEMPLATE_EXAMPLES_DIR,
    TEST_DATA_DIR,
)
from ..test_templates import (
    template_set,
    template,
    template_example,
    template_example_xlsx_path,
)
from ..test_assays import ARTIFACT_OBJ


def prismify_test_set(filter=None):
    yielded = False

    for template, xlsx_path in template_set():

        if filter and template.type not in filter:
            continue

        xlsx, errors = XlTemplateReader.from_excel(xlsx_path)
        assert not errors
        yield xlsx, template
        yielded = True

    if not yielded:
        raise Exception(f"no prismify test for filter {filter!r} found")


TEST_PRISM_TRIAL = {
    PROTOCOL_ID_FIELD_NAME: "test_prism_trial_id",
    "allowed_collection_event_names": ["Baseline", "Pre_Day_1_Cycle_2"],
    "allowed_cohort_names": ["Arm_Z", "Arm_A"],
    "participants": [
        {
            "cimac_participant_id": "CTTTPP1",
            "participant_id": "TTTPP103",
            "cohort_name": "Arm_Z",
            "samples": [
                {
                    "sample_volume_units": "Other",
                    "material_used": 1,
                    "material_remaining": 0,
                    "quality_of_sample": "Other",
                    "aliquots": [
                        {
                            "slide_number": "1",
                            "aliquot_replacement": "N/A",
                            "aliquot_status": "Other",
                        }
                    ],
                    "cimac_id": "CTTTPP111.00",
                    "parent_sample_id": "test_sample_1",
                    "collection_event_name": "Baseline",
                    "sample_location": "---",
                    "type_of_sample": "Other",
                    "type_of_primary_container": "Other",
                }
            ],
        },
        {
            "samples": [
                {
                    "sample_volume_units": "Other",
                    "material_used": 2,
                    "material_remaining": 0,
                    "quality_of_sample": "Other",
                    "aliquots": [
                        {
                            "slide_number": "1",
                            "aliquot_replacement": "N/A",
                            "aliquot_status": "Other",
                        }
                    ],
                    "cimac_id": "CTTTPP121.00",
                    "parent_sample_id": "test_sample_2",
                    "collection_event_name": "Baseline",
                    "sample_location": "---",
                    "type_of_sample": "Other",
                    "type_of_primary_container": "Other",
                }
            ],
            "cimac_participant_id": "CTTTPP2",
            "participant_id": "TTTPP203",
            "cohort_name": "Arm_Z",
        },
        {
            "samples": [
                {
                    "sample_volume_units": "Other",
                    "material_used": 2,
                    "material_remaining": 0,
                    "quality_of_sample": "Other",
                    "aliquots": [
                        {
                            "slide_number": "1",
                            "aliquot_replacement": "N/A",
                            "aliquot_status": "Other",
                        }
                    ],
                    "cimac_id": "CTTTPP122.00",
                    "parent_sample_id": "test_sample_3",
                    "collection_event_name": "Baseline",
                    "sample_location": "---",
                    "type_of_sample": "Other",
                    "type_of_primary_container": "Other",
                }
            ],
            "cimac_participant_id": "CTTTPP3",
            "participant_id": "TTTPP303",
            "cohort_name": "Arm_Z",
        },
        {
            "samples": [
                {
                    "sample_volume_units": "Other",
                    "material_used": 2,
                    "material_remaining": 0,
                    "quality_of_sample": "Other",
                    "aliquots": [
                        {
                            "slide_number": "1",
                            "aliquot_replacement": "N/A",
                            "aliquot_status": "Other",
                        }
                    ],
                    "cimac_id": "CTTTPP123.00",
                    "parent_sample_id": "test_sample_3",
                    "collection_event_name": "Baseline",
                    "sample_location": "---",
                    "type_of_sample": "Other",
                    "type_of_primary_container": "Other",
                }
            ],
            "cimac_participant_id": "CTTTPP4",
            "participant_id": "TTTPP403",
            "cohort_name": "Arm_Z",
        },
    ],
    "assays": {
        "wes": [
            {
                "assay_creator": "Mount Sinai",
                "paired_end_reads": "Paired",
                "read_length": 100,
                "sequencer_platform": "Illumina - HiSeq 3000",
                "library_kit": "Hyper Prep ICE Exome Express: 1.0",
                "sequencing_protocol": "Express Somatic Human WES (Deep Coverage) v1.1",
                "bait_set": "whole_exome_illumina_coding_v1",
                "records": [
                    {
                        "sequencing_date": "2019-01-01 00:00:00",
                        "quality_flag": 1,
                        "cimac_id": "CTTTPP111.00",
                        "files": {
                            "r1": [
                                {"upload_placeholder": "r1.1_0"},
                                {"upload_placeholder": "r1.1_1"},
                            ],
                            "r2": [{"upload_placeholder": "r2.1_0"}],
                        },
                    },
                    {
                        "sequencing_date": "2019-01-01 00:00:00",
                        "quality_flag": 1,
                        "cimac_id": "CTTTPP121.00",
                        "files": {
                            "r1": [
                                {"upload_placeholder": "r1.2_0"},
                                {"upload_placeholder": "r1.2_1"},
                            ],
                            "r2": [{"upload_placeholder": "r2.2_0"}],
                        },
                    },
                ],
            }
        ],
        "rna": [
            {
                "assay_creator": "Mount Sinai",
                "enrichment_method": "Ribo minus",
                "enrichment_vendor_kit": "Agilent",
                "paired_end_reads": "Paired",
                "sequencer_platform": "Illumina - HiSeq 3000",
                "records": [
                    {
                        "quality_flag": 1,
                        "cimac_id": "CTTTPP122.00",
                        "library_yield_ng": 666,
                        "dv200": 0.7,
                        "rqs": 8,
                        "rin": 8,
                        "files": {
                            "r1": [
                                {"upload_placeholder": "r1.1_0"},
                                {"upload_placeholder": "r1.1_1"},
                            ],
                            "r2": [{"upload_placeholder": "r2.1_0"}],
                        },
                    },
                    {
                        "quality_flag": 1,
                        "library_yield_ng": 666,
                        "dv200": 0.7,
                        "rqs": 8,
                        "rin": 8,
                        "cimac_id": "CTTTPP123.00",
                        "files": {
                            "r1": [
                                {"upload_placeholder": "r1.2_0"},
                                {"upload_placeholder": "r1.2_1"},
                            ],
                            "r2": [{"upload_placeholder": "r2.2_0"}],
                        },
                    },
                ],
            }
        ],
    },
}


# corresponding list of gs_urls.
WES_TEMPLATE_EXAMPLE_GS_URLS = {
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/wes/CTTTPP111.00/r1_0.fastq.gz": "r1.1_0",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/wes/CTTTPP111.00/r1_1.fastq.gz": "r1.1_1",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/wes/CTTTPP111.00/r2_0.fastq.gz": "r2.1_0",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/wes/CTTTPP121.00/r1_0.fastq.gz": "r1.2_0",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/wes/CTTTPP121.00/r1_1.fastq.gz": "r1.2_1",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/wes/CTTTPP121.00/r2_0.fastq.gz": "r2.2_0",
}

WESBAM_TEMPLATE_EXAMPLE_GS_URLS = {
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/wes/CTTTPP111.00/reads_0.bam": "bam_whatever_1_0",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/wes/CTTTPP111.00/reads_1.bam": "bam_whatever_1_1",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/wes/CTTTPP121.00/reads_0.bam": "bam_whatever_2_0",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/wes/CTTTPP121.00/reads_1.bam": "bam_whatever_2_1",
}

RNA_TEMPLATE_EXAMPLE_GS_URLS = {
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/rna/CTTTPP122.00/r1_0.fastq.gz": "r1.1_0",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/rna/CTTTPP122.00/r1_1.fastq.gz": "r1.1_1",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/rna/CTTTPP122.00/r2_0.fastq.gz": "r2.1_0",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/rna/CTTTPP123.00/r1_0.fastq.gz": "r1.2_0",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/rna/CTTTPP123.00/r1_1.fastq.gz": "r1.2_1",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/rna/CTTTPP123.00/r2_0.fastq.gz": "r2.2_0",
}

RNABAM_TEMPLATE_EXAMPLE_GS_URLS = {
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/rna/CTTTPP122.00/reads_0.bam": "bam_whatever_1_0",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/rna/CTTTPP122.00/reads_1.bam": "bam_whatever_1_1",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/rna/CTTTPP123.00/reads_0.bam": "bam_whatever_2_0",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    + "/rna/CTTTPP123.00/reads_1.bam": "bam_whatever_2_1",
}

NUM_ARTIFACT_FIELDS = 8


def test_test_data():

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    validator.validate(TEST_PRISM_TRIAL)


def test_merge_core():

    # create aliquot
    aliquot = {
        "slide_number": "12",
        "aliquot_replacement": "N/A",
        "aliquot_status": "Other",
    }

    # create the sample.
    sample = {
        "cimac_id": "CTTTPPP12.34",
        "parent_sample_id": "blank",
        "aliquots": [aliquot],
        "collection_event_name": "Baseline",
        "sample_location": "---",
        "type_of_sample": "Other",
        "type_of_primary_container": "Other",
        "sample_volume_units": "Other",
        "material_used": 1,
        "material_remaining": 0,
        "quality_of_sample": "Other",
    }

    # create the participant
    participant = {
        "cimac_participant_id": "CTTTPPP",
        "participant_id": "blank",
        "samples": [sample],
        "cohort_name": "Arm_Z",
    }

    # create the trial
    ct1 = {
        PROTOCOL_ID_FIELD_NAME: "test",
        "participants": [participant],
        "allowed_collection_event_names": ["Baseline"],
        "allowed_cohort_names": ["Arm_Z"],
    }

    # create validator assert schemas are valid.
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema
    validator.validate(ct1)

    # create a copy of this, modify participant id
    ct2 = copy.deepcopy(ct1)
    ct2["participants"][0]["cimac_participant_id"] = "PABCD"

    # merge them
    merger = Merger(schema, strategies=core.PRISM_PRISMIFY_STRATEGIES)
    ct3 = merger.merge(ct1, ct2)

    # assert we have two participants and their ids are different.
    assert len(ct3["participants"]) == 2
    assert (
        ct3["participants"][0]["cimac_participant_id"]
        == ct1["participants"][0]["cimac_participant_id"]
    )
    assert (
        ct3["participants"][1]["cimac_participant_id"]
        == ct2["participants"][0]["cimac_participant_id"]
    )

    # now lets add a new sample to one of the participants
    ct4 = copy.deepcopy(ct3)
    ct4["participants"][0]["samples"][0]["cimac_id"] = "new_id_1"

    ct5 = merger.merge(ct3, ct4)
    assert len(ct5["participants"][0]["samples"]) == 2

    # now lets add a new aliquot to one of the samples.
    ct6 = copy.deepcopy(ct5)
    aliquot2 = ct6["participants"][0]["samples"][0]["aliquots"][0]
    aliquot2["slide_number"] = "new_ali_id_1"

    ct7 = merger.merge(ct5, ct6)
    assert len(ct7["participants"][0]["samples"][0]["aliquots"]) == 2


MINIMAL_TEST_TRIAL = {
    PROTOCOL_ID_FIELD_NAME: "minimal",
    "allowed_collection_event_names": ["Baseline"],
    "allowed_cohort_names": ["Arm_Z"],
    "participants": [
        {
            "samples": [
                {
                    "aliquots": [
                        {
                            "slide_number": "1",
                            "aliquot_replacement": "N/A",
                            "aliquot_status": "Other",
                        }
                    ],
                    "sample_volume_units": "Other",
                    "material_used": 1,
                    "material_remaining": 0,
                    "quality_of_sample": "Other",
                    "collection_event_name": "Baseline",
                    "sample_location": "---",
                    "type_of_sample": "Other",
                    "type_of_primary_container": "Other",
                    "parent_sample_id": "test_min_Sample_1",
                    "cimac_id": "CTTTMIN01.00",
                }
            ],
            "cimac_participant_id": "CTTTMIN",
            "participant_id": "test_min_Patient_1",
            "cohort_name": "Arm_Z",
        }
    ],
}


def test_minimal_test_data():
    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    validator.validate(MINIMAL_TEST_TRIAL)


def test_samples_merge():

    # one with 1 sample
    a1 = copy.deepcopy(MINIMAL_TEST_TRIAL)

    # create a2 and modify ids to trigger merge behavior
    a2 = copy.deepcopy(a1)
    a2["participants"][0]["samples"][0]["cimac_id"] = "something different"

    # create validator assert schema is valid.
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # merge them
    merger = Merger(schema, strategies=core.PRISM_PRISMIFY_STRATEGIES)
    a3 = merger.merge(a1, a2)
    assert len(a3["participants"]) == 1
    assert len(a3["participants"][0]["samples"]) == 2


def repr_if_template(param):
    return repr(param) if isinstance(param, Template) else "example"


@pytest.mark.parametrize("xlsx, template", prismify_test_set(), ids=repr_if_template)
def test_prism(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # TODO: every other assay
    if template.type not in SUPPORTED_ASSAYS:
        return

    # turn into object.
    ct, file_maps, errs = prismify(xlsx, template)
    assert 0 == len(errs)

    if template.type in SUPPORTED_ASSAYS:
        # olink is different - is will never have array of assay "runs" - only one
        if template.type != "olink":

            # also handle WES & RNA differently due to two templates mapping to one assay
            ttype = template.type
            if template.type == "wes_bam" or template.type == "wes_fastq":
                ttype = "wes"

            elif template.type == "rna_bam" or template.type == "rna_fastq":
                ttype = "rna"

            # this assert the merging of rows in the template is happening properly
            # multiple entries means the merge didn't work
            assert len(ct["assays"][ttype]) == 1

    elif template.type in SUPPORTED_SHIPPING_MANIFESTS:
        assert not ct.get("assays"), "Assay created during manifest prismify"

    else:
        assert False, f"Unknown template {template.type}"

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema, strategies=core.PRISM_PRISMIFY_STRATEGIES)
    merged = merger.merge(TEST_PRISM_TRIAL, ct)

    validator.validate(merged)
    # assert works
    errors = list(validator.iter_errors(merged))
    assert not errors

    if template.type in SUPPORTED_ASSAYS:
        assert merged[PROTOCOL_ID_FIELD_NAME] == "test_prism_trial_id"
    else:
        assert (
            TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME] == merged[PROTOCOL_ID_FIELD_NAME]
        )

    return merged, file_maps


@pytest.mark.parametrize("xlsx, template", prismify_test_set(), ids=repr_if_template)
def test_filepath_gen(xlsx, template):

    # TODO: every other assay
    if template.type not in SUPPORTED_ASSAYS:
        return

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    _, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0
    # we ignore and do not validate 'ct'
    # because it's only a ct patch not a full ct

    local_to_gcs_mapping = {}
    for fmap_entry in file_maps:
        local_to_gcs_mapping[fmap_entry.gs_key] = fmap_entry

    assert len(local_to_gcs_mapping) == len(file_maps), "gcs_key/url collision"

    # Check that `gcs_uri_format`s in {assay}_templates.json
    # put all artifacts within "BUCKET/{trial_id}/{assay}" folder
    # because cloud-function access granting depends on that
    prefixes = ["/".join(fmap_entry.gs_key.split("/")[:2]) for entry in file_maps]
    trial_id = TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]
    assay_prefix = template.type.split("_")[0]
    assert set(prefixes) == {f"{trial_id}/{assay_prefix}"}

    # assert we have the right file counts etc.
    if template.type == "wes_fastq":

        # we should have 2 .fastq files per sample.
        assert 2 == sum([x.gs_key.endswith("/r1_0.fastq.gz") for x in file_maps])
        # we should have 4 file total for forward, because we have
        # a list of two local files for each sample in wes example xlsx.
        assert 4 == sum(
            [
                x.gs_key.endswith("/r1_0.fastq.gz")
                or x.gs_key.endswith("/r1_1.fastq.gz")
                for x in file_maps
            ]
        )
        # and only 2 total for reverse (r2) - each sample has just 1.
        assert 2 == sum([x.gs_key.endswith("/r2_0.fastq.gz") for x in file_maps])

        # Local files in total:
        assert 6 == sum([x.local_path.endswith(".fastq.gz") for x in file_maps])
        assert len(file_maps) == 6
        assert 6 == sum(
            [
                x.gs_key.startswith(TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME])
                for x in file_maps
            ]
        )

        # all that with
        # 1 trial id
        assert 1 == len(set([x.gs_key.split("/")[0] for x in file_maps]))
        # 2 samples

        assert ["CTTTPP111.00", "CTTTPP121.00"] == list(
            sorted(set([x.gs_key.split("/")[2] for x in file_maps]))
        )

    elif template.type == "wes_bam":

        # we should have 2 bam in each (2) sample.
        assert 4 == sum([x.gs_key.endswith(".bam") for x in file_maps])

        # in total local
        assert 4 == sum([x.local_path.endswith(".bam") for x in file_maps])

        # 2 in total
        assert len(file_maps) == 4
        assert 4 == sum(
            [
                x.gs_key.startswith(TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME])
                for x in file_maps
            ]
        )

        # all that with
        # 1 trial id
        assert 1 == len(set([x.gs_key.split("/")[0] for x in file_maps]))
        # 2 samples

        assert ["CTTTPP111.00", "CTTTPP121.00"] == list(
            sorted(set([x.gs_key.split("/")[2] for x in file_maps]))
        )

    elif template.type == "rna_fastq":
        # we should have 2 .fastq files per sample.
        assert 2 == sum([x.gs_key.endswith("/r1_0.fastq.gz") for x in file_maps])

        # we should have 4 file total for forward, because we have
        # a list of two local files for each sample in wes example xlsx.
        assert 4 == sum(
            [
                x.gs_key.endswith("/r1_0.fastq.gz")
                or x.gs_key.endswith("/r1_1.fastq.gz")
                for x in file_maps
            ]
        )

        # and only 2 total for reverse (r2) - each sample has just 1.
        assert 2 == sum([x.gs_key.endswith("/r2_0.fastq.gz") for x in file_maps])

        # Local files in total:
        assert 6 == sum([x.local_path.endswith(".fastq.gz") for x in file_maps])
        assert len(file_maps) == 6
        assert 6 == sum(
            [
                x.gs_key.startswith(TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME])
                for x in file_maps
            ]
        )

        # all that with 1 trial id
        assert 1 == len(set([x.gs_key.split("/")[0] for x in file_maps]))

        # 2 samples
        assert ["CTTTPP122.00", "CTTTPP123.00"] == list(
            sorted(set([x.gs_key.split("/")[2] for x in file_maps]))
        )

    elif template.type == "rna_bam":

        # we should have 2 bam in each (2) sample.
        assert 4 == sum([x.gs_key.endswith(".bam") for x in file_maps])

        # in total local
        assert 4 == sum([x.local_path.endswith(".bam") for x in file_maps])

        # 2 in total
        assert len(file_maps) == 4
        assert 4 == sum(
            [
                x.gs_key.startswith(TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME])
                for x in file_maps
            ]
        )

        # all that with
        # 1 trial id
        assert 1 == len(set([x.gs_key.split("/")[0] for x in file_maps]))
        # 2 samples

        assert ["CTTTPP122.00", "CTTTPP123.00"] == list(
            sorted(set([x.gs_key.split("/")[2] for x in file_maps]))
        )

    elif template.type == "elisa":

        # we should have 1 xlsx file
        assert 1 == len(file_maps)
        assert file_maps[0].gs_key.endswith("/assay.xlsx")
        assert file_maps[0].gs_key.startswith(TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME])

    elif template.type == "olink":

        # we should have 2 npx files
        assert 2 == sum([x.gs_key.endswith("assay_npx.xlsx") for x in file_maps])

        # we should have 2 raw_ct files
        assert 2 == sum([x.gs_key.endswith("assay_raw_ct.csv") for x in file_maps])

        # 4 assay level + 1 combined in tots
        assert 5 == sum([x.local_path.startswith("olink_assay") for x in file_maps])

        # we should have 1 study level npx
        assert 1 == sum([x.gs_key.endswith("study_npx.xlsx") for x in file_maps])

        # check the number of files - 1 study + 2*(npx + ct raw)
        assert len(file_maps) == 5
        assert 5 == sum([x.gs_key.startswith("test_prism_trial_id") for x in file_maps])

    elif template.type == "cytof":
        # TODO: UPdate this to assert we can handle multiple source fcs files

        for x in file_maps:
            assert x.gs_key.endswith(".fcs")
        assert len(file_maps) == 6

    elif template.type == "ihc":
        assert 1 == sum([x.gs_key.endswith(".tif") for x in file_maps])
        assert 1 == sum([x.gs_key.endswith(".tiff") for x in file_maps])
        assert 1 == sum([x.gs_key.endswith(".qptiff") for x in file_maps])
        assert 1 == sum([x.gs_key.endswith(".svs") for x in file_maps])

    elif template.type in SUPPORTED_SHIPPING_MANIFESTS:

        assert len(file_maps) == 0

    else:
        assert False, f"add {template.type} assay specific asserts"


@pytest.mark.parametrize(
    "xlsx, template", prismify_test_set("cytof"), ids=repr_if_template
)
def test_prismify_cytof_only(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    ct, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0

    # we should have 7 files:
    # * 2 raw fcs files (batch-level)
    # * 2 normalized and debarcoded fcs files (sample-level)
    # * 2 processed fcs files (sample-level)
    assert len(file_maps) == 6

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema, strategies=core.PRISM_PRISMIFY_STRATEGIES)
    merged = merger.merge(TEST_PRISM_TRIAL, ct)

    # assert works
    validator.validate(merged)


@pytest.mark.parametrize(
    "xlsx, template", prismify_test_set("ihc"), ids=repr_if_template
)
def test_prismify_ihc(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    ct, file_maps, errs = prismify(xlsx, template)

    for e in validator.iter_errors(ct):
        assert isinstance(e, InDocRefNotFoundError) or (  # not found cimac_ids
            "'participants'" in str(e)
            and "required" in str(e)  # or no "participants" found.
        )

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema, strategies=core.PRISM_PRISMIFY_STRATEGIES)
    merged = merger.merge(TEST_PRISM_TRIAL, ct)

    # assert works
    validator.validate(merged)


@pytest.mark.parametrize(
    "xlsx, template", prismify_test_set("plasma"), ids=repr_if_template
)
def test_prismify_plasma(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    # parse the spreadsheet and get the file maps
    md_patch, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0
    with pytest.raises(Exception):
        validator.validate(md_patch)

    md_patch["allowed_collection_event_names"] = TEST_PRISM_TRIAL[
        "allowed_collection_event_names"
    ]
    md_patch["allowed_cohort_names"] = TEST_PRISM_TRIAL["allowed_cohort_names"]
    validator.validate(md_patch)

    assert file_maps == []
    assert 2 == len(md_patch["participants"])
    assert 3 == len(md_patch["participants"][0]["samples"])

    p = md_patch["participants"][0]
    assert (
        participant_id_from_cimac(p["samples"][0]["cimac_id"])
        == p["cimac_participant_id"]
    )

    assert p["gender"]  # filled from 1 tab
    assert p["cohort_name"]  # filled from another

    assert p["samples"][0]["processed_sample_id"]  # filled from 1 tab
    assert p["samples"][0]["topography_code"]  # filled from the second tab
    assert p["samples"][0]["site_description"]  # filled from the second tab


def assert_only_indocref_exceptions(exceptions: list):
    assert 0 == len([e for e in exceptions if not isinstance(e, InDocRefNotFoundError)])


@pytest.mark.parametrize(
    "xlsx, template", prismify_test_set(filter=["wes_bam"]), ids=repr_if_template
)
def test_prismify_wesbam_only(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    md_patch, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0

    # md patch is not complete
    # but errors should be only
    for e in validator.iter_errors(md_patch):
        if isinstance(e, InDocRefNotFoundError):
            # not found cimac_ids - we expect that
            continue
        elif "'participants' is a required" in str(e):
            # or no "participants" found - we expect that
            continue
        elif "'allowed_" in str(e) and "is a required" in str(e):
            # or allowed_cohort_names and allowed_collection_event_names defined in TEST_PRISM_TRIAL base - we expect that
            continue
        else:
            raise Exception(e)

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema, strategies=core.PRISM_PRISMIFY_STRATEGIES)
    merged = merger.merge(TEST_PRISM_TRIAL, md_patch)

    # assert works
    validator.validate(merged)

    merged_wo_needed_participants = copy.deepcopy(merged)
    merged_wo_needed_participants["participants"][0]["samples"][0][
        "cimac_id"
    ] = "CTTTNAADA.00"

    # assert in_doc_ref constraints work
    with pytest.raises(InDocRefNotFoundError):
        validator.validate(merged_wo_needed_participants)

    assert_only_indocref_exceptions(
        validator.iter_errors(merged_wo_needed_participants)
    )


@pytest.mark.parametrize(
    "xlsx, template", prismify_test_set("wes_fastq"), ids=repr_if_template
)
def test_prismify_wesfastq_only(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    md_patch, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0

    for e in validator.iter_errors(md_patch):
        assert isinstance(e, InDocRefNotFoundError) or (
            "'participants'" in str(e) and "required" in str(e)
        )

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema, strategies=core.PRISM_PRISMIFY_STRATEGIES)
    merged = merger.merge(TEST_PRISM_TRIAL, md_patch)

    # assert works
    validator.validate(merged)

    merged_wo_needed_participants = copy.deepcopy(merged)
    merged_wo_needed_participants["participants"][0]["samples"][0][
        "cimac_id"
    ] = "CTTTNAADA.00"

    # assert in_doc_ref constraints work
    with pytest.raises(InDocRefNotFoundError):
        validator.validate(merged_wo_needed_participants)

    assert_only_indocref_exceptions(
        validator.iter_errors(merged_wo_needed_participants)
    )


@pytest.mark.parametrize(
    "xlsx, template", prismify_test_set(filter=["rna_bam"]), ids=repr_if_template
)
def test_prismify_rnabam_only(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    md_patch, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0

    # md patch is not complete
    # but errors should be only
    for e in validator.iter_errors(md_patch):
        assert isinstance(e, InDocRefNotFoundError) or (  # not found cimac_ids
            "'participants'" in str(e)
            and "required" in str(e)  # or no "participants" found.
        )

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema, strategies=core.PRISM_PRISMIFY_STRATEGIES)
    merged = merger.merge(TEST_PRISM_TRIAL, md_patch)

    # assert works
    validator.validate(merged)

    merged_wo_needed_participants = copy.deepcopy(merged)
    merged_wo_needed_participants["participants"][0]["samples"][0][
        "cimac_id"
    ] = "CTTTNAADA.00"

    # assert in_doc_ref constraints work
    with pytest.raises(InDocRefNotFoundError):
        validator.validate(merged_wo_needed_participants)


@pytest.mark.parametrize(
    "xlsx, template", prismify_test_set("rna_fastq"), ids=repr_if_template
)
def test_prismify_rnafastq_only(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    md_patch, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0

    for e in validator.iter_errors(md_patch):
        assert isinstance(e, InDocRefNotFoundError) or (
            "'participants'" in str(e) and "required" in str(e)
        )

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema, strategies=core.PRISM_PRISMIFY_STRATEGIES)
    merged = merger.merge(TEST_PRISM_TRIAL, md_patch)

    # assert works
    validator.validate(merged)

    merged_wo_needed_participants = copy.deepcopy(merged)
    merged_wo_needed_participants["participants"][0]["samples"][0][
        "cimac_id"
    ] = "CTTTNAADA.00"

    # assert in_doc_ref constraints work
    with pytest.raises(InDocRefNotFoundError):
        validator.validate(merged_wo_needed_participants)


@pytest.mark.parametrize(
    "xlsx, template", prismify_test_set("olink"), ids=repr_if_template
)
def test_prismify_olink_only(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    ct, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema, strategies=core.PRISM_PRISMIFY_STRATEGIES)
    merged = merger.merge(MINIMAL_TEST_TRIAL, ct)

    # assert works
    validator.validate(merged)

    # return these for use in other tests
    return ct, file_maps


def test_merge_artifact_none_md5():
    """Ensure merge artifact doesn't fail if either md5 or crc32c is None"""
    # create the clinical trial.
    ct_1 = copy.deepcopy(TEST_PRISM_TRIAL)
    ct_2 = copy.deepcopy(TEST_PRISM_TRIAL)
    ct_3 = copy.deepcopy(TEST_PRISM_TRIAL)

    # create validator
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    validator.validate(ct_1)

    url, uuid = list(WES_TEMPLATE_EXAMPLE_GS_URLS.items())[0]
    common_args = dict(
        assay_type="wes",
        artifact_uuid=uuid,
        object_url=url,
        file_size_bytes=1,
        uploaded_timestamp="01/01/2001",
    )

    # when md5_hash is None
    ct_1, artifact, patch_metadata = merge_artifact(
        ct_1, **common_args, md5_hash=None, crc32c_hash=f"hash_{uuid}"
    )
    validator.validate(ct_1)

    # when crc32c_hash is None
    ct_2, artifact, patch_metadata = merge_artifact(
        ct_2, **common_args, md5_hash=f"hash_{uuid}", crc32c_hash=None
    )
    validator.validate(ct_2)

    # when both are None
    with pytest.raises(
        AssertionError, match="Either crc32c_hash or md5_hash must be provided"
    ):
        ct_3, artifact, patch_metadata = merge_artifact(
            ct_3, **common_args, md5_hash=None, crc32c_hash=None
        )


def test_merge_artifact_wesfastq_benchmark(benchmark):
    ct = copy.deepcopy(TEST_PRISM_TRIAL)
    url, uuid = list(WES_TEMPLATE_EXAMPLE_GS_URLS.items())[0]

    def merge():
        merge_artifact(
            ct,
            assay_type="wes",
            artifact_uuid=uuid,
            object_url=url,
            file_size_bytes=1,
            uploaded_timestamp="01/01/2001",
            md5_hash=f"hash_{uuid}",
            crc32c_hash=f"hash_{uuid}",
        )

    benchmark.pedantic(merge, rounds=10)


def test_merge_artifact_wesfastq_only():

    # create the clinical trial.
    ct = copy.deepcopy(TEST_PRISM_TRIAL)

    # create validator
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    validator.validate(ct)

    # loop over each url
    searched_urls = []
    for url, uuid in WES_TEMPLATE_EXAMPLE_GS_URLS.items():

        # attempt to merge
        ct, artifact, patch_metadata = merge_artifact(
            ct,
            assay_type="wes",
            artifact_uuid=uuid,
            object_url=url,
            file_size_bytes=1,
            uploaded_timestamp="01/01/2001",
            md5_hash=f"hash_{uuid}",
            crc32c_hash=f"hash_{uuid}",
        )

        # assert we still have a good clinical trial object.
        validator.validate(ct)

        # check that the data_format was set
        assert "data_format" in artifact

        # search for this url and all previous (no clobber)
        searched_urls.append(url)

    for url in searched_urls:
        assert len((ct | grep(url))["matched_values"]) > 0

    assert (
        len(ct["assays"]["wes"]) == 1
    ), "Multiple WESes created instead of merging into one"
    assert len(ct["assays"]["wes"][0]["records"]) == 2, "More records than expected"

    dd = DeepDiff(TEST_PRISM_TRIAL, ct)

    # we add 7 required fields per artifact thus `*7`
    assert (
        len(dd["dictionary_item_added"])
        == len(WES_TEMPLATE_EXAMPLE_GS_URLS) * NUM_ARTIFACT_FIELDS
    ), "Unexpected CT changes"

    assert list(dd.keys()) == ["dictionary_item_added"], "Unexpected CT changes"


def test_merge_ct_meta():
    """ 
    tests merging of two clinical trial metadata
    objects. Currently this test only supports
    WES but other tests should be added in the
    future
    """

    # create two clinical trials
    patch = copy.deepcopy(TEST_PRISM_TRIAL)
    target = copy.deepcopy(TEST_PRISM_TRIAL)

    # first test the fact that base doc must be valid
    del target["participants"]
    with pytest.raises(InvalidMergeTargetException):
        merge_clinical_trial_metadata(patch, target)

    with pytest.raises(InvalidMergeTargetException):
        merge_clinical_trial_metadata(patch, {})

    # next assert the merge is only happening on the same trial
    patch[PROTOCOL_ID_FIELD_NAME] = "not_the_same"
    target = copy.deepcopy(TEST_PRISM_TRIAL)
    with pytest.raises(InvalidMergeTargetException):
        merge_clinical_trial_metadata(patch, target)

    # revert the data to same key trial id but
    # include data in 1 that is missing in the other
    # at the trial level and assert the merge
    # does not clobber any
    patch[PROTOCOL_ID_FIELD_NAME] = target[PROTOCOL_ID_FIELD_NAME]
    patch["trial_name"] = "name ABC"
    target["nci_id"] = "xyz1234"

    ct_merge, errs = merge_clinical_trial_metadata(patch, target)
    assert not errs
    assert ct_merge["trial_name"] == "name ABC"
    assert ct_merge["nci_id"] == "xyz1234"

    # updates aren't allowed
    patch["trial_name"] = "name ABC"
    target["trial_name"] = "CBA eman"
    with pytest.raises(
        MergeCollisionException, match="conflicting values for trial_name"
    ):
        merge_clinical_trial_metadata(patch, target)
    target["trial_name"] = patch["trial_name"]

    # now change the participant ids
    # this should cause the merge to have two
    # participants.
    patch["participants"][0]["cimac_participant_id"] = "CTTTDD1"
    for i, sample in enumerate(patch["participants"][0]["samples"]):
        sample["cimac_id"] = f"CTTTDD1S{i}.00"

    ct_merge, errs = merge_clinical_trial_metadata(patch, target)
    assert not errs
    assert len(ct_merge["participants"]) == 1 + len(TEST_PRISM_TRIAL["participants"])

    # now lets have the same participant but adding multiple samples.
    patch[PROTOCOL_ID_FIELD_NAME] = target[PROTOCOL_ID_FIELD_NAME]
    patch["participants"][0]["cimac_participant_id"] = target["participants"][0][
        "cimac_participant_id"
    ]
    patch["participants"][0]["samples"][0]["cimac_id"] = "CTTTPP1N1.00"
    patch["participants"][1]["samples"][0]["cimac_id"] = "CTTTPP1N2.00"

    ct_merge, errs = merge_clinical_trial_metadata(patch, target)
    assert not errs
    assert len(ct_merge["participants"]) == len(TEST_PRISM_TRIAL["participants"])
    assert sum(len(p["samples"]) for p in ct_merge["participants"]) == 2 + sum(
        len(p["samples"]) for p in TEST_PRISM_TRIAL["participants"]
    )


@pytest.mark.parametrize("xlsx, template", prismify_test_set(), ids=repr_if_template)
def test_end_to_end_prismify_merge_artifact_merge(xlsx, template):

    assert template.type in SUPPORTED_TEMPLATES

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    # parse the spreadsheet and get the file maps
    prism_patch, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0

    if (
        template.type in SUPPORTED_MANIFESTS
        and template.type not in SUPPORTED_SHIPPING_MANIFESTS
    ):
        if template.type == "tumor_normal_pairing":
            assert prism_patch["analysis"]["wes_analysis"]
            assert len(prism_patch["analysis"]["wes_analysis"]["pair_runs"]) == 1
            assert (
                len(
                    set(
                        pair["run_id"]
                        for pair in prism_patch["analysis"]["wes_analysis"]["pair_runs"]
                    )
                )
                == 1
            )

        else:
            assert 0, f"add {template.type} manifest specific test asserts"

    if template.type in SUPPORTED_SHIPPING_MANIFESTS:
        assert len(prism_patch["shipments"]) == 1

        p0 = prism_patch["participants"][0]
        assert (
            participant_id_from_cimac(p0["samples"][0]["cimac_id"])
            == p0["cimac_participant_id"]
        )

        if template.type == "pbmc":
            assert len(prism_patch["participants"]) == 2
            assert len(p0["samples"]) == 3
            assert len(prism_patch["participants"][1]["samples"]) == 3

        elif template.type == "plasma":
            assert len(prism_patch["participants"]) == 2
            assert len(p0["samples"]) == 3
            assert "aliquots" not in p0["samples"][0]

        elif template.type == "normal_blood_dna":
            assert len(prism_patch["participants"]) == 2
            assert len(p0["samples"]) == 3

        elif template.type == "normal_tissue_dna":
            assert len(prism_patch["participants"]) == 2
            assert len(p0["samples"]) == 3

        elif template.type == "tumor_tissue_dna":
            assert len(prism_patch["participants"]) == 2
            assert len(p0["samples"]) == 3

        elif template.type == "tissue_slide":
            assert len(prism_patch["participants"]) == 2
            assert len(p0["samples"]) == 3

        elif template.type == "h_and_e":
            assert len(prism_patch["participants"]) == 1
            assert len(p0["samples"]) == 2

        else:
            assert False, f"add {template.type} specific asserts"

    if template.type in SUPPORTED_ASSAYS:
        # olink is different in structure - no array of assays, only one.
        if template.type == "olink":
            prism_patch_assay_records = prism_patch["assays"][template.type]["records"]
            assert len(prism_patch_assay_records) == 2

        elif template.type == "elisa":
            prism_patch_assay_records = prism_patch["assays"][template.type]
            assert len(prism_patch_assay_records) == 1

        elif template.type == "cytof":
            assert len(prism_patch["assays"][template.type]) == 1
            assert "records" in prism_patch["assays"][template.type][0]
            assert len(prism_patch["assays"][template.type][0]["records"]) == 2
            assert len(prism_patch["assays"][template.type][0]["cytof_antibodies"]) == 2

        elif template.type == "wes_fastq":
            assert len(prism_patch["assays"]["wes"][0]["records"]) == 2
        elif template.type == "wes_bam":
            assert len(prism_patch["assays"]["wes"][0]["records"]) == 2

        elif template.type == "rna_fastq":
            assert len(prism_patch["assays"]["rna"][0]["records"]) == 2
        elif template.type == "rna_bam":
            assert len(prism_patch["assays"]["rna"][0]["records"]) == 2

        elif template.type == "ihc":
            assert len(prism_patch["assays"][template.type][0]["records"]) == 4

        else:
            raise NotImplementedError(
                f"no support in test for this template.type {template.type}"
            )

    for f in file_maps:
        ttype = template.type
        if ttype == "wes_bam" or ttype == "wes_fastq":
            ttype = "wes"
        elif ttype == "rna_bam" or ttype == "rna_fastq":
            ttype = "rna"
        assert f"{ttype}/" in f.gs_key, f"No {ttype} template.type found"

    original_ct = copy.deepcopy(TEST_PRISM_TRIAL)

    if template.type in SUPPORTED_ANALYSES:
        # we can't merge analysis info unless an associated initial assay upload exists
        # in the clinical trial object, so we add an initial assay upload below:

        if template.type == "cytof_analysis":
            # simulate an initial cytof upload by prismifying the initial cytof template object,
            # and merging it with clinical trial object
            cytof_input_xlsx_path = os.path.join(
                TEMPLATE_EXAMPLES_DIR, "cytof_template.xlsx"
            )
            cytof_input_xlsx, _ = XlTemplateReader.from_excel(cytof_input_xlsx_path)
            cytof_input_template = Template.from_type("cytof")
            cytof_input_patch, _, _ = prismify(cytof_input_xlsx, cytof_input_template)

            original_ct, errs = merge_clinical_trial_metadata(
                cytof_input_patch, original_ct
            )
            assert len(errs) == 0

        elif template.type == "wes_analysis":
            # simulate an initial WES upload by prismifying the initial WES template object,
            # and merging it with clinical trial object
            wes_input_xlsx_path = os.path.join(
                TEMPLATE_EXAMPLES_DIR, "wes_fastq_template.xlsx"
            )
            wes_input_xlsx, _ = XlTemplateReader.from_excel(wes_input_xlsx_path)
            wes_input_template = Template.from_type("wes_fastq")
            wes_input_patch, _, _ = prismify(wes_input_xlsx, wes_input_template)

            original_ct, errs = merge_clinical_trial_metadata(
                wes_input_patch, original_ct
            )
            assert len(errs) == 0

        else:
            raise NotImplementedError(
                f"no support in test for this template.type {template.type}"
            )

    # "prismify" provides only a patch so we need to merge it into a "full" ct
    full_after_prism, errs = merge_clinical_trial_metadata(prism_patch, original_ct)
    assert not errs

    # Assert we still have a good clinical trial object, so we can save it.
    validator.validate(full_after_prism)

    patch_copy_4_artifacts = copy.deepcopy(prism_patch)

    # now we simulate that upload was successful
    merged_gs_keys = []
    for i, fmap_entry in enumerate(file_maps):
        # attempt to merge
        patch_copy_4_artifacts, artifact, patch_metadata = merge_artifact(
            patch_copy_4_artifacts,
            artifact_uuid=fmap_entry.upload_placeholder,
            object_url=fmap_entry.gs_key,
            assay_type=template.type,
            file_size_bytes=i,
            uploaded_timestamp="01/01/2001",
            md5_hash=f"hash_{i}",
            crc32c_hash=f"hash_{i}",
        )

        # check that the data_format was set
        assert "data_format" in artifact

        # assert we still have a good clinical trial object, so we can save it
        step_ct, errs = merge_clinical_trial_metadata(
            patch_copy_4_artifacts, original_ct
        )
        assert not errs
        validator.validate(step_ct)

        # we will than search for this url in the resulting ct,
        # to check all artifacts were indeed merged
        merged_gs_keys.append(fmap_entry.gs_key)

    # `merge_artifact` modifies ct in-place, so
    full_ct, errs = merge_clinical_trial_metadata(patch_copy_4_artifacts, original_ct)
    assert not errs

    # validate the full clinical trial object
    validator.validate(full_ct)

    if template.type == "ihc":
        assert len(merged_gs_keys) == 4

    elif template.type == "wes_fastq":
        assert (
            len(merged_gs_keys) == 3 * 2
        )  # 2 files for forward + 1 for rev, per entry/sample in xlsx
        assert set(merged_gs_keys) == set(WES_TEMPLATE_EXAMPLE_GS_URLS.keys())

    elif template.type == "wes_bam":
        assert len(merged_gs_keys) == 2 * 2  # 2 files per entry in xlsx
        assert set(merged_gs_keys) == set(WESBAM_TEMPLATE_EXAMPLE_GS_URLS.keys())

    elif template.type == "rna_fastq":
        assert (
            len(merged_gs_keys) == 3 * 2
        )  # 2 files for forward + 1 for rev, per entry/sample in xlsx
        assert set(merged_gs_keys) == set(RNA_TEMPLATE_EXAMPLE_GS_URLS.keys())

    elif template.type == "rna_bam":
        assert len(merged_gs_keys) == 2 * 2  # 2 files per entry in xlsx
        assert set(merged_gs_keys) == set(RNABAM_TEMPLATE_EXAMPLE_GS_URLS.keys())

    elif template.type == "olink":
        # 2 files per entry in xlsx + 1 file in preamble
        assert len(merged_gs_keys) == 5

    elif template.type == "elisa":
        # 1 xlsx file in preamble
        assert len(merged_gs_keys) == 1

    elif template.type in SUPPORTED_MANIFESTS:
        assert len(merged_gs_keys) == 0

    elif template.type == "cytof":
        # TODO: This will need ot be updated when we accept a list of source fcs files
        assert len(merged_gs_keys) == 6  # 6 output files

    elif template.type == "cytof_analysis":
        assert (
            len(merged_gs_keys) == 16
        )  # 2 run level + (7 sample level * 2 samples) output files

    elif template.type == "wes_analysis":
        # 14 (for each run) + 15 (for each tumor sample) + 15 (for each normal sample))
        assert len(merged_gs_keys) == 2 * (14 + (15 * 2))

    else:
        assert False, f"add {template.type} assay specific asserts on 'merged_gs_keys'"

    for file_map_entry in file_maps:
        assert (
            len((full_ct | grep(fmap_entry.gs_key))["matched_values"]) == 1
        )  # each gs_url only once

    # olink is special - it's not an array
    if template.type == "olink":
        assert (
            len(full_ct["assays"][template.type]["records"]) == 2
        ), "More records than expected"

    elif template.type == "wes_bam" or template.type == "wes_fastq":
        ttype = "wes"
        assert len(full_ct["assays"][ttype]) == 1 + len(
            TEST_PRISM_TRIAL["assays"][ttype]
        ), f"Multiple {ttype}-assays created instead of merging into one"
        assert (
            len(full_ct["assays"][ttype][0]["records"]) == 2
        ), "More records than expected"

    elif template.type == "rna_bam" or template.type == "rna_fastq":
        ttype = "rna"
        assert len(full_ct["assays"][ttype]) == 1 + len(
            TEST_PRISM_TRIAL["assays"][ttype]
        ), f"Multiple {ttype}-assays created instead of merging into one"
        assert (
            len(full_ct["assays"][ttype][0]["records"]) == 2
        ), "More records than expected"

    elif template.type == "ihc":
        assert (
            len(full_ct["assays"][template.type][0]["records"]) == 4
        ), "More records than expected"

    elif template.type in SUPPORTED_MANIFESTS:
        assert full_ct["assays"] == original_ct["assays"]

    elif template.type == "cytof":
        assert len(full_ct["assays"][template.type]) == 1

    elif template.type == "cytof_analysis":
        # the original CyTOF upload had 2 records, hence after analysis, it's analysis has 2 records
        assert (
            len(full_ct["assays"]["cytof"][0]["records"]) == 2
        ), "More records than expected"

    elif template.type == "wes_analysis":
        # the original WES upload had 2 records, hence after analysis, it's analysis has 2 records
        assert (
            len(full_ct["assays"]["wes"][0]["records"]) == 2
        ), "More records than expected"

    elif template.type == "elisa":
        assert len(full_ct["assays"]["elisa"]) == 1, "More assay runs than expected"
        assert (
            len(full_ct["assays"]["elisa"][0]["antibodies"]) == 2
        ), "More antibodies than expected"

    else:
        assert False, f"add {template.type} assay specific asserts on 'full_ct'"

    dd = DeepDiff(full_after_prism, full_ct)

    if template.type == "wes_fastq":

        # 6 files * 7 artifact attributes
        assert (
            len(dd["dictionary_item_added"]) == 6 * NUM_ARTIFACT_FIELDS
        ), "Unexpected CT changes"

        # nothing else in diff
        assert list(dd.keys()) == ["dictionary_item_added"], "Unexpected CT changes"

    elif template.type == "wes_bam":

        # 4 files * 7 artifact attributes
        assert (
            len(dd["dictionary_item_added"]) == 4 * NUM_ARTIFACT_FIELDS
        ), "Unexpected CT changes"

        # nothing else in diff
        assert list(dd.keys()) == ["dictionary_item_added"], "Unexpected CT changes"

    elif template.type == "rna_fastq":
        # 6 files * 7 artifact attributes
        assert (
            len(dd["dictionary_item_added"]) == 6 * NUM_ARTIFACT_FIELDS
        ), "Unexpected CT changes"

        # nothing else in diff
        assert list(dd.keys()) == ["dictionary_item_added"], "Unexpected CT changes"

    elif template.type == "rna_bam":

        # 4 files * 7 artifact attributes
        assert (
            len(dd["dictionary_item_added"]) == 4 * NUM_ARTIFACT_FIELDS
        ), "Unexpected CT changes"

        # nothing else in diff
        assert list(dd.keys()) == ["dictionary_item_added"], "Unexpected CT changes"

    elif template.type == "ihc":
        # 2 files * 7 artifact attributes
        assert (
            len(dd["dictionary_item_added"]) == 4 * NUM_ARTIFACT_FIELDS
        ), "Unexpected CT changes"

    elif template.type == "olink":

        assert list(dd.keys()) == ["dictionary_item_added"], "Unexpected CT changes"

        # 7 artifact attributes * 5 files (2 per record + 1 study)
        assert len(dd["dictionary_item_added"]) == NUM_ARTIFACT_FIELDS * (
            2 * 2 + 1
        ), "Unexpected CT changes"

    elif template.type == "elisa":

        assert list(dd.keys()) == ["dictionary_item_added"], "Unexpected CT changes"

        # artifact attributes for just one artifact elisa xlsx file
        assert (
            len(dd["dictionary_item_added"]) == NUM_ARTIFACT_FIELDS
        ), "Unexpected CT changes"

    elif template.type in SUPPORTED_MANIFESTS:
        assert len(dd) == 0, "Unexpected CT changes"

    elif template.type == "cytof":
        # 7 artifact attributes * 6 files
        assert (
            len(dd["dictionary_item_added"]) == NUM_ARTIFACT_FIELDS * 6
        ), "Unexpected CT changes"

    elif template.type == "cytof_analysis":
        # 7 artifact attributes * 16 files
        assert (
            len(dd["dictionary_item_added"]) == NUM_ARTIFACT_FIELDS * 16
        ), "Unexpected CT changes"

    elif template.type == "wes_analysis":
        # 7 artifact attributes * 2*(14+(15*2)) files
        assert len(dd["dictionary_item_added"]) == NUM_ARTIFACT_FIELDS * 2 * (
            14 + (15 * 2)
        ), "Unexpected CT changes"

    else:
        assert False, f"add {template.type} assay specific asserts"
