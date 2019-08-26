#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for PRISM the module which pulls JSON objects from excel spreadsheets."""

import os
import copy
import pytest
import jsonschema
import json
from deepdiff import grep, DeepDiff
from pprint import pprint
from jsonmerge import Merger

from cidc_schemas.prism import prismify, merge_artifact
from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader

from .constants import ROOT_DIR, SCHEMA_DIR, TEMPLATE_EXAMPLES_DIR
from .test_templates import template_paths
from .test_assays import ARTIFACT_OBJ


CLINICAL_TRIAL = {
        "lead_organization_study_id": "10021",
        "participants": [
            {
                "samples": [
                    {
                        "aliquots": [
                            {
                                "cimac_aliquot_id": "aliquot 1",
                                "units": "Other",
                                "material_used": 1,
                                "material_remaining": 0,
                                "aliquot_quality_status": "Other",
                                "aliquot_replacement": "N/A",
                                "aliquot_status": "Other"
                            },
                        ],
                        "cimac_sample_id": "sample 1",
                        "site_sample_id": "site sample 1",
                        "time_point": "---",
                        "sample_location": "---",
                        "specimen_type": "Other",
                        "specimen_format": "Other",
                        "genomic_source": "Tumor",
                    },
                    {
                        "aliquots": [
                            {
                                "cimac_aliquot_id": "aliquot 2",
                                "units": "Other",
                                "material_used": 2,
                                "material_remaining": 0,
                                "aliquot_quality_status": "Other",
                                "aliquot_replacement": "N/A",
                                "aliquot_status": "Other"
                            }
                        ],
                        "cimac_sample_id": "sample 2",
                        "site_sample_id": "site sample 2",
                        "time_point": "---",
                        "sample_location": "---",
                        "specimen_type": "Other",
                        "specimen_format": "Other",
                        "genomic_source": "Tumor",
                    }
                ],
                "cimac_participant_id": "patient 1",
                "trial_participant_id": "trial patient 1",
                "cohort_id": "---",
                "arm_id": "---"
            }
        ],
        "assays": {
            "wes": [
                {
                    "assay_creator": "Mount Sinai",
                    "enrichment_vendor_kit": "Twist",
                    "library_vendor_kit": "KAPA - Hyper Prep",
                    "sequencer_platform": "Illumina - NextSeq 550",
                    "paired_end_reads": "Paired",
                    "read_length": 100,
                    "records": [
                        {
                            "library_kit_lot": "lib lot 1",
                            "enrichment_vendor_lot": "enrich lot 1",
                            "library_prep_date": "2019-01-01 00:00:00",
                            "capture_date": "2019-01-01 00:00:00",
                            "input_ng": 101,
                            "library_yield_ng": 701,
                            "average_insert_size": 251,
                            "cimac_participant_id": "patient 1",
                            "cimac_sample_id": "sample 1",
                            "cimac_aliquot_id": "aliquot 1",
                            "files": {
                                "fastq_1": {
                                    "upload_placeholder": "fastq_1.1"
                                },
                                "fastq_2": {
                                    "upload_placeholder": "fastq_2.1"
                                },
                                "read_group_mapping_file": {
                                    "upload_placeholder": "read_group_mapping_file.1"
                                }
                            }
                        },
                        {
                            "library_kit_lot": "lib lot 2",
                            "enrichment_vendor_lot": "enrich lot 2",
                            "library_prep_date": "2019-02-02 00:00:00",
                            "capture_date": "2019-02-02 00:00:00",
                            "input_ng": 102,
                            "library_yield_ng": 702,
                            "average_insert_size": 252,
                            "cimac_participant_id": "patient 1",
                            "cimac_sample_id": "sample 2",
                            "cimac_aliquot_id": "aliquot 2",
                            "files": {
                                "fastq_1": {
                                    "upload_placeholder": "fastq_1.2"
                                },
                                "fastq_2": {
                                    "upload_placeholder": "fastq_2.2"
                                },
                                "read_group_mapping_file": {
                                    "upload_placeholder": "read_group_mapping_file.2"
                                }
                            }
                        }
                    ]
                }
            ]
        }
    }


def test_merge_core():

    # create aliquot
    aliquot = {
        "cimac_aliquot_id": "1234",
        "units": "Other",
        "material_used": 1,
        "material_remaining": 0,
        "aliquot_quality_status": "Other",
        "aliquot_replacement": "N/A",
        "aliquot_status": "Other"
    }

    # create the sample.
    sample = {
        "cimac_sample_id": "S1234",
        "site_sample_id": "blank",
        "aliquots": [aliquot],
        "time_point": "---",
        "sample_location": "---",
        "specimen_type": "Other",
        "specimen_format": "Other",
        "genomic_source": "Tumor",
    }

    # create the participant
    participant = {
        "cimac_participant_id": "P1234",
        "trial_participant_id": "blank",
        "samples": [sample],
        "cohort_id": "---",
        "arm_id": "---"
    }

    # create the trial
    ct1 = {
        "lead_organization_study_id": "test",
        "participants": [participant]
    }

    # create validator assert schemas are valid.
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema
    validator.validate(ct1)

    # create a copy of this, modify participant id
    ct2 = copy.deepcopy(ct1)
    ct2['participants'][0]['cimac_participant_id'] = "PABCD"

    # merge them
    merger = Merger(schema)
    ct3 = merger.merge(ct1, ct2)

    # assert we have two participants and their ids are different.
    assert len(ct3['participants']) == 2
    assert ct3['participants'][0]['cimac_participant_id'] == ct1['participants'][0]['cimac_participant_id']
    assert ct3['participants'][1]['cimac_participant_id'] == ct2['participants'][0]['cimac_participant_id']

    # now lets add a new sample to one of the participants
    ct4 = copy.deepcopy(ct3)
    sample2 = ct4['participants'][0]['samples'][0]
    sample2['cimac_sample_id'] = 'new_id_1'

    ct5 = merger.merge(ct3, ct4)
    assert len(ct5['participants'][0]['samples']) == 2

    # now lets add a new aliquot to one of the samples.
    ct6 = copy.deepcopy(ct5)
    aliquot2 = ct6['participants'][0]['samples'][0]['aliquots'][0]
    aliquot2['cimac_aliquot_id'] = 'new_ali_id_1'

    ct7 = merger.merge(ct5, ct6)
    assert len(ct7['participants'][0]['samples'][0]['aliquots']) == 2


MINIMAL_CT_1PA1SA1AL = {
    "lead_organization_study_id": "minimal",
    "participants": [
        {
            "samples": [
                {
                    "aliquots": [
                        {
                            "cimac_aliquot_id": "Aliquot 1",
                            "units": "Other",
                            "material_used": 1,
                            "material_remaining": 0,
                            "aliquot_quality_status": "Other",
                            "aliquot_replacement": "N/A",
                            "aliquot_status": "Other"
                        }
                    ],
                    "genomic_source": "Tumor",
                    "time_point": "---",
                    "sample_location": "---",
                    "specimen_type": "Other",
                    "specimen_format": "Other",
                    "site_sample_id": "site Sample 1",
                    "cimac_sample_id": "Sample 1"
                }
            ],
            "cimac_participant_id": "Patient 1",
            "trial_participant_id": "trial Patient 1",
            "cohort_id": "---",
            "arm_id": "---"
        }
    ]
}
def test_samples_merge():

    # one with 1 sample
    a1 = copy.deepcopy(MINIMAL_CT_1PA1SA1AL)
    
    # create a2 and modify ids to trigger merge behavior
    a2 = copy.deepcopy(a1)
    a2['participants'][0]['samples'][0]['cimac_sample_id'] = "something different"

    # create validator assert schema is valid.
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # merge them
    merger = Merger(schema)
    a3 = merger.merge(a1, a2)
    assert len(a3['participants']) == 1
    assert len(a3['participants'][0]['samples']) == 2


@pytest.mark.parametrize('schema_path, xlsx_path', template_paths())
def test_prism(schema_path, xlsx_path):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # extract hint.
    hint = schema_path.split("/")[-1].replace("_template.json", "")

    # TODO: only implemented WES parsing...
    if hint != "wes":
        return

    # turn into object.
    ct, file_maps = prismify(xlsx_path, schema_path, assay_hint=hint)

    assert len(ct['assays']['wes']) == 1
    
    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema)
    merged = merger.merge(MINIMAL_CT_1PA1SA1AL, ct)

    # assert works
    validator.validate(merged)

@pytest.mark.parametrize('schema_path, xlsx_path', template_paths())
def test_filepath_gen_wes_only(schema_path, xlsx_path):
    # extract hint.
    hint = schema_path.split("/")[-1].replace("_template.json", "")

    # TODO: only implemented WES parsing...
    if hint != "wes":
        return

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    _, file_maps = prismify(xlsx_path, schema_path, assay_hint=hint)
    # we ignore and do not validate 'ct' 
    # because it's only a ct patch not a full ct 

    # assert we have the right counts.
    if hint == "wes":

        # check the number of files present.
        assert len(file_maps) == 6

        # we should have 2 fastq per sample.
        # we should have 2 tot forward.
        assert 2 == sum([1 for x in file_maps if x['gs_key'].endswith("fastq_1")])
        # we should have 2 tot rev.
        assert 2 == sum([1 for x in file_maps if x['gs_key'].endswith("fastq_2")])

        # we should have 2 text files
        assert 2 == sum([1 for x in file_maps if x['gs_key'].endswith("read_group_mapping_file")])
    


def test_prismify_wes_only():

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # create the example template.
    temp_path = os.path.join(SCHEMA_DIR, 'templates', 'metadata', 'wes_template.json')
    xlsx_path = os.path.join(TEMPLATE_EXAMPLES_DIR, "wes_template.xlsx")
    hint = 'wes'

    # parse the spreadsheet and get the file maps
    ct, file_maps = prismify(xlsx_path, temp_path, assay_hint=hint)

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema)
    merged = merger.merge(MINIMAL_CT_1PA1SA1AL, ct)

    # assert works
    validator.validate(merged)


def test_merge_artifact_wes_only():

    # create the clinical trial.
    ct = copy.deepcopy(CLINICAL_TRIAL)

    # define list of gs_urls.
    urls = [
        '10021/patient 1/sample 1/aliquot 1/wes/fastq_1',
        '10021/patient 1/sample 1/aliquot 1/wes/fastq_2',
        '10021/patient 1/sample 1/aliquot 1/wes/read_group_mapping_file',
        '10021/patient 1/sample 2/aliquot 2/wes/fastq_1',
        '10021/patient 1/sample 2/aliquot 2/wes/fastq_2',
        '10021/patient 1/sample 2/aliquot 2/wes/read_group_mapping_file'
    ]

    # create validator
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    validator.validate(ct)

    # loop over each url
    searched_urls = []
    for i, url in enumerate(urls):

        # attempt to merge
        ct = merge_artifact(
                ct,
                object_url=url,
                assay="wes", # TODO figure out how to know that prior to calling?
                file_size_bytes=i,
                uploaded_timestamp="01/01/2001",
                md5_hash=f"hash_{i}"
            )

        # assert we still have a good clinical trial object.
        validator.validate(ct)

        # search for this url and all previous (no clobber)
        searched_urls.append(url)

    for url in searched_urls:
        assert len((ct | grep(url))['matched_values']) > 0

    assert len(ct['assays']['wes']) == 1, "Multiple WESes created instead of merging into one"
    assert len(ct['assays']['wes'][0]['records']) == 2, "More records than expected"

    dd = DeepDiff(CLINICAL_TRIAL,ct)

    # we add 6 required fields per artifact thus `*6`
    assert len(dd['dictionary_item_added']) == len(urls)*6, "Unexpected CT changes"

    # in the process upload_placeholder gets removed per artifact
    assert len(dd['dictionary_item_removed']) == len(urls), "Unexpected CT changes"
    assert list(dd.keys()) == ['dictionary_item_added', 'dictionary_item_removed'], "Unexpected CT changes"

@pytest.mark.parametrize('schema_path, xlsx_path', template_paths())
def test_end_to_end_wes_only(schema_path, xlsx_path):
    # extract hint
    hint = schema_path.split("/")[-1].replace("_template.json", "")

    # TODO: implement other than WES parsing...
    if hint != "wes":
        return 

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema
    merger = Merger(schema)

    # parse the spreadsheet and get the file maps
    prism_patch, file_maps = prismify(xlsx_path, schema_path, assay_hint=hint)

    assert len(prism_patch['assays']['wes']) == 1
    assert len(prism_patch['assays']['wes'][0]['records']) == 2
    for f in file_maps:
        assert f'/{hint}/' in f['gs_key'], f"No {hint} hint found"

    # assert we still have a good clinical trial object, so we can save it
    # but we need to merge it, because "prismify" provides only a patch
    after_prism = merger.merge(CLINICAL_TRIAL, prism_patch)
    validator.validate(after_prism)

    after_prism_copy = copy.deepcopy(after_prism)

    #now we simulate that upload was successful 
    searched_urls = []
    for i, fmap_entry in enumerate(file_maps):

        # attempt to merge
        after_prism_w_artifact = merge_artifact(
                after_prism_copy,
                object_url=fmap_entry['gs_key'],
                assay=hint, # TODO figure out how to know that prior to calling?
                file_size_bytes=i,
                uploaded_timestamp="01/01/2001",
                md5_hash=f"hash_{i}"
            )

        # assert we still have a good clinical trial object, so we can save it
        validator.validate(after_prism_w_artifact)

        # we will than search for this url in the resulting ct, 
        # to check all artifacts were indeed merged
        searched_urls.append(fmap_entry['gs_key'])

    # `merge_artifact` modifies ct in-place, so 
    full_ct = after_prism_w_artifact


    assert len(searched_urls) == 3*2 # 3 files per entry in xlsx

    for url in searched_urls:
        assert len((full_ct | grep(url))['matched_values']) == 1 # each gs_url only once  

    assert len(full_ct['assays']['wes']) == 1+len(CLINICAL_TRIAL['assays']['wes']), "Multiple WESes created instead of merging into one"
    assert len(full_ct['assays']['wes'][0]['records']) == 2, "More records than expected"

    dd = DeepDiff(after_prism, full_ct)

    # 6 files * 6 artifact atributes
    assert len(dd['dictionary_item_added']) == 6*6, "Unexpected CT changes"

    # in the process upload_placeholder gets removed per artifact = 6
    assert len(dd['dictionary_item_removed']) == len(searched_urls), "Unexpected CT changes"

    # nothing else in diff
    assert list(dd.keys()) == ['dictionary_item_added', 'dictionary_item_removed'], "Unexpected CT changes"





