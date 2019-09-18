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

from cidc_schemas.prism import prismify, merge_artifact, \
    merge_clinical_trial_metadata, InvalidMergeTargetException, \
    SUPPORTED_ASSAYS, SUPPORTED_MANIFESTS, SUPPORTED_TEMPLATES
from cidc_schemas.json_validation import load_and_validate_schema, InDocRefNotFoundError
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader

from .constants import ROOT_DIR, SCHEMA_DIR, TEMPLATE_EXAMPLES_DIR
from .test_templates import template_paths
from .test_assays import ARTIFACT_OBJ


TEST_PRISM_TRIAL = {
        "lead_organization_study_id": "test_prism_trial_id",
        "participants": [
            {
                "cimac_participant_id": "test_PA_1",
                "trial_participant_id": "test_trial_patient_1",
                "cohort_id": "---",
                "arm_id": "---",
                "samples": [
                    {
                        "aliquots": [
                            {
                                "cimac_aliquot_id": "test_AL_1.1.1",
                                "units": "Other",
                                "material_used": 1,
                                "material_remaining": 0,
                                "aliquot_quality_status": "Other",
                                "aliquot_replacement": "N/A",
                                "aliquot_status": "Other"
                            },
                        ],
                        "cimac_sample_id": "test_SA_1.1",
                        "site_sample_id": "test_sample_1",
                        "time_point": "---",
                        "sample_location": "---",
                        "specimen_type": "Other",
                        "specimen_format": "Other",
                        "genomic_source": "Tumor",
                    }
                ],
            },
            {
                "samples": [
                    {
                        "aliquots": [
                            {
                                "cimac_aliquot_id": "test_AL_1.2.1",
                                "units": "Other",
                                "material_used": 2,
                                "material_remaining": 0,
                                "aliquot_quality_status": "Other",
                                "aliquot_replacement": "N/A",
                                "aliquot_status": "Other"
                            }
                        ],
                        "cimac_sample_id": "test_SA_2.1",
                        "site_sample_id": "test_sample_2",
                        "time_point": "---",
                        "sample_location": "---",
                        "specimen_type": "Other",
                        "specimen_format": "Other",
                        "genomic_source": "Tumor",
                    }
                ],
                "cimac_participant_id": "test_PA_2",
                "trial_participant_id": "test_trial_patient_2",
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
                            "cimac_participant_id": "test_PA_1",
                            "cimac_sample_id": "test_SA_1.1",
                            "cimac_aliquot_id": "test_AL_1.1.1",
                            "files": {
                                "r1": {
                                    "upload_placeholder": "r1.1"
                                },
                                "r2": {
                                    "upload_placeholder": "r2.1"
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
                            "cimac_participant_id": "test_PA_2",
                            "cimac_sample_id": "test_SA_2.1",
                            "cimac_aliquot_id": "test_AL_1.2.1",
                            "files": {
                                "r1": {
                                    "upload_placeholder": "r1.2"
                                },
                                "r2": {
                                    "upload_placeholder": "r2.2"
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


# corresponding list of gs_urls.
WES_TEMPLATE_EXAMPLE_GS_URLS = {
    TEST_PRISM_TRIAL["lead_organization_study_id"]+'/test_PA_1/test_SA_1.1/test_AL_1.1.1/wes/r1.fastq': 
    "r1.1",
    TEST_PRISM_TRIAL["lead_organization_study_id"]+'/test_PA_1/test_SA_1.1/test_AL_1.1.1/wes/r2.fastq': 
    "r2.1",
    TEST_PRISM_TRIAL["lead_organization_study_id"]+'/test_PA_1/test_SA_1.1/test_AL_1.1.1/wes/rgm.txt': 
    "read_group_mapping_file.1",
    TEST_PRISM_TRIAL["lead_organization_study_id"]+'/test_PA_2/test_SA_2.1/test_AL_1.2.1/wes/r1.fastq': 
    "r1.2",
    TEST_PRISM_TRIAL["lead_organization_study_id"]+'/test_PA_2/test_SA_2.1/test_AL_1.2.1/wes/r2.fastq': 
    "r2.2",
    TEST_PRISM_TRIAL["lead_organization_study_id"]+'/test_PA_2/test_SA_2.1/test_AL_1.2.1/wes/rgm.txt': 
    "read_group_mapping_file.2"
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


MINIMAL_TEST_TRIAL = {
    "lead_organization_study_id": "minimal",
    "participants": [
        {
            "samples": [
                {
                    "aliquots": [
                        {
                            "cimac_aliquot_id": "test_min_AL_1.1.1",
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
                    "site_sample_id": "test_min_Sample_1",
                    "cimac_sample_id": "test_min_SA_1.1"
                }
            ],
            "cimac_participant_id": "test_min_PA_1",
            "trial_participant_id": "test_min_Patient_1",
            "cohort_id": "---",
            "arm_id": "---"
        }
    ]
}


def test_samples_merge():

    # one with 1 sample
    a1 = copy.deepcopy(MINIMAL_TEST_TRIAL)
    
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

    # TODO: every other assay
    if hint not in SUPPORTED_ASSAYS:
        return

    # turn into object.
    ct, file_maps = prismify(xlsx_path, schema_path, assay_hint=hint)
    if hint == 'cytof':
        assert "CYTOF_TEST1" == ct['lead_organization_study_id']
        ct['lead_organization_study_id'] = 'test_prism_trial_id'

    if hint in SUPPORTED_ASSAYS:
        # olink is different - is will never have array of assay "runs" - only one
        if hint != 'olink':
            assert len(ct['assays'][hint]) == 1

    elif hint in SUPPORTED_MANIFESTS:
        assert not ct.get('assays'), "Assay created during manifest prismify"

    else:
        assert False, f"Unknown template {hint}"

    
    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema)
    merged = merger.merge(TEST_PRISM_TRIAL, ct)

    # assert works
    errors = list(validator.iter_errors(merged))
    assert not errors 

    if hint in SUPPORTED_ASSAYS :
        assert merged["lead_organization_study_id"] == "test_prism_trial_id"
    else:
        assert TEST_PRISM_TRIAL["lead_organization_study_id"] == merged["lead_organization_study_id"]


@pytest.mark.parametrize('schema_path, xlsx_path', template_paths())
def test_unsupported_prismify(schema_path, xlsx_path):
    # extract hint
    hint = schema_path.split("/")[-1].replace("_template.json", "")

    # skipp supported
    if hint in SUPPORTED_TEMPLATES:
        return

    with pytest.raises(NotImplementedError):
        prismify(xlsx_path, schema_path, assay_hint=hint)



@pytest.mark.parametrize('schema_path, xlsx_path', template_paths())
def test_filepath_gen(schema_path, xlsx_path):
    # extract hint.
    hint = schema_path.split("/")[-1].replace("_template.json", "")

    # TODO: every other assay
    if hint not in SUPPORTED_ASSAYS:
        return

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    _, file_maps = prismify(xlsx_path, schema_path, assay_hint=hint)
    # we ignore and do not validate 'ct' 
    # because it's only a ct patch not a full ct 

    local_to_gcs_mapping = {}
    for fmap_entry in file_maps:
        local_to_gcs_mapping[fmap_entry.gs_key] = fmap_entry

    assert len(local_to_gcs_mapping) == len(file_maps), "gcs_key/url collision"
    

    # assert we have the right file counts etc.
    if hint == "wes":

        # we should have 2 fastq per sample.
        # we should have 2 tot forward.
        assert 2 == sum([x.gs_key.endswith("/r1.fastq") for x in file_maps])
        # we should have 2 tot rev.
        assert 2 == sum([x.gs_key.endswith("/r2.fastq") for x in file_maps])
        # in total local
        assert 4 == sum([x.local_path.endswith(".fastq") for x in file_maps])

        # we should have 2 text files
        assert 2 == sum([x.gs_key.endswith("/rgm.txt") for x in file_maps])
        assert 2 == sum([x.local_path.endswith(".txt") for x in file_maps])

        # 4 in total
        assert len(file_maps) == 6
        assert 6 == sum([x.gs_key.startswith(TEST_PRISM_TRIAL["lead_organization_study_id"]) for x in file_maps])

        # all that with
        # 1 trial id
        assert 1 == len(set([x.gs_key.split("/")[0] for x in file_maps]))
        # 2 participants
        assert 2 == len(set([x.gs_key.split("/")[1] for x in file_maps]))
        # 2 samples
        assert 2 == len(set([x.gs_key.split("/")[2] for x in file_maps]))
        # 2 aliquots
        assert 2 == len(set([x.gs_key.split("/")[3] for x in file_maps]))

    elif hint == 'olink':

        # we should have 2 npx files
        assert 2 == sum([x.gs_key.endswith("assay_npx.xlsx") for x in file_maps])

        # we should have 2 raw_ct files
        assert 2 == sum([x.gs_key.endswith("assay_raw_ct.xlsx") for x in file_maps])

        # 4 assay level in tots
        assert 4 == sum([x.local_path.startswith("Olink_assay") for x in file_maps])

        # we should have 1 study level npx
        assert 1 == sum([x.gs_key.endswith("study_npx.xlsx") for x in file_maps])

        # check the number of files - 1 study + 2*(npx + ct raw)
        assert len(file_maps) == 5
        assert 5 == sum([x.gs_key.startswith("test_prism_trial_id") for x in file_maps])

    elif hint == 'cytof':
        # TODO: UPdate this to assert we can handle multiple source fcs files
        for x in file_maps:
            assert x.gs_key.endswith(".fcs")
        assert len(file_maps) == 6

    elif hint in SUPPORTED_MANIFESTS:

        assert len(file_maps) == 0

    else:
        assert False, f"add {hint} assay specific asserts"


def test_prismify_cytof_only():

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # create the example template.
    hint = 'cytof'
    temp_path = os.path.join(SCHEMA_DIR, 'templates', 'metadata', f'{hint}_template.json')
    xlsx_path = os.path.join(TEMPLATE_EXAMPLES_DIR, f"{hint}_template.xlsx")

    # parse the spreadsheet and get the file maps
    ct, file_maps = prismify(xlsx_path, temp_path, assay_hint=hint, verb=False)

    # we should have 3 files, the processed fcs and two source fcs X2
    assert len(file_maps) == 6

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema)
    merged = merger.merge(TEST_PRISM_TRIAL, ct)

    # assert works
    validator.validate(merged)



def test_prismify_wes_only():

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # create the example template.
    temp_path = os.path.join(SCHEMA_DIR, 'templates', 'metadata', 'wes_template.json')
    xlsx_path = os.path.join(TEMPLATE_EXAMPLES_DIR, "wes_template.xlsx")
    hint = 'wes'

    # parse the spreadsheet and get the file maps
    md_patch, file_maps = prismify(xlsx_path, temp_path, assay_hint=hint)

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema)
    merged = merger.merge(TEST_PRISM_TRIAL, md_patch)

    # assert works
    validator.validate(merged)


    merged_wo_needed_participants = copy.deepcopy(merged)
    merged_wo_needed_participants['participants'][0]['samples'].pop()

    # assert in_doc_ref constraints work
    with pytest.raises(InDocRefNotFoundError):
        validator.validate(merged_wo_needed_participants)

    # 2 record = 2 missing aliquot refs = 2 errors
    assert 2 == len(list(validator.iter_errors(merged_wo_needed_participants)))
    


def test_merge_artifact_wes_only():

    # create the clinical trial.
    ct = copy.deepcopy(TEST_PRISM_TRIAL)

    # create validator
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    validator.validate(ct)

    # loop over each url
    searched_urls = []
    for url, uuid in WES_TEMPLATE_EXAMPLE_GS_URLS.items():

        # attempt to merge
        ct, artifact = merge_artifact(
                ct,
                assay_type="wes",
                artifact_uuid=uuid,
                object_url=url,
                file_size_bytes=1,
                uploaded_timestamp="01/01/2001",
                md5_hash=f"hash_{uuid}"
            )

        # assert we still have a good clinical trial object.
        validator.validate(ct)

        # check that the data_format was set
        assert 'data_format' in artifact

        # search for this url and all previous (no clobber)
        searched_urls.append(url)

    for url in searched_urls:
        assert len((ct | grep(url))['matched_values']) > 0

    assert len(ct['assays']['wes']) == 1, "Multiple WESes created instead of merging into one"
    assert len(ct['assays']['wes'][0]['records']) == 2, "More records than expected"

    dd = DeepDiff(TEST_PRISM_TRIAL,ct)

    # we add 7 required fields per artifact thus `*7`
    assert len(dd['dictionary_item_added']) == len(WES_TEMPLATE_EXAMPLE_GS_URLS)*7, "Unexpected CT changes"

    assert list(dd.keys()) == ['dictionary_item_added'], "Unexpected CT changes"

def test_merge_ct_meta():
    """ 
    tests merging of two clinical trial metadata
    objects. Currently this test only supports
    WES but other tests should be added in the
    future
    """

    # create two clinical trials
    ct1 = copy.deepcopy(TEST_PRISM_TRIAL)
    ct2 = copy.deepcopy(TEST_PRISM_TRIAL)

    # first test the fact that base doc must be valid
    del ct2['participants']
    with pytest.raises(InvalidMergeTargetException):
        merge_clinical_trial_metadata(ct1, ct2)

    with pytest.raises(InvalidMergeTargetException):
        merge_clinical_trial_metadata(ct1, {})

    # next assert the merge is only happening on the same trial
    ct1["lead_organization_study_id"] = "not_the_same"
    ct2 = copy.deepcopy(TEST_PRISM_TRIAL)
    with pytest.raises(RuntimeError):
        merge_clinical_trial_metadata(ct1, ct2)

    # revert the data to same key trial id but
    # include data in 1 that is missing in the other
    # at the trial level and assert the merge
    # does not clobber any
    ct1["lead_organization_study_id"] = ct2["lead_organization_study_id"] 
    ct1['trial_name'] = 'name ABC'
    ct2['nci_id'] = 'xyz1234'

    ct_merge = merge_clinical_trial_metadata(ct1, ct2)
    assert ct_merge['trial_name'] == 'name ABC'
    assert ct_merge['nci_id'] == 'xyz1234'

    # assert the patch over-writes the original value
    # when value is present in both objects
    ct1['trial_name'] = 'name ABC'
    ct2['trial_name'] = 'CBA eman'

    ct_merge = merge_clinical_trial_metadata(ct1, ct2)
    assert ct_merge['trial_name'] == 'name ABC'

    # now change the participant ids
    # this should cause the merge to have two
    # participants.
    ct1['participants'][0]['cimac_participant_id'] = 'different_id'

    ct_merge = merge_clinical_trial_metadata(ct1, ct2)
    assert len(ct_merge['participants']) == 1+len(TEST_PRISM_TRIAL['participants'])

    # now lets have the same participant but adding multiple samples.
    ct1["lead_organization_study_id"] = ct2["lead_organization_study_id"] 
    ct1['participants'][0]['cimac_participant_id'] = \
        ct2['participants'][0]['cimac_participant_id']
    ct1['participants'][0]['samples'][0]['cimac_sample_id'] = 'new_id_1'
    ct1['participants'][1]['samples'][0]['cimac_sample_id'] = 'new_id_2'
 
    ct_merge = merge_clinical_trial_metadata(ct1, ct2)
    assert len(ct_merge['participants']) == len(TEST_PRISM_TRIAL['participants'])
    assert sum(len(p['samples']) for p in ct_merge['participants']) == 2+sum(len(p['samples']) for p in TEST_PRISM_TRIAL['participants'])


@pytest.mark.parametrize('schema_path, xlsx_path', template_paths())
def test_end_to_end_prismify_merge_artifact_merge(schema_path, xlsx_path):

    # extract hint
    hint = schema_path.split("/")[-1].replace("_template.json", "")

    # TODO: implement other assays
    if hint not in SUPPORTED_TEMPLATES:
        return 

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    
    # parse the spreadsheet and get the file maps
    prism_patch, file_maps = prismify(xlsx_path, schema_path, assay_hint=hint, verb=False)

    if hint in SUPPORTED_MANIFESTS:
        assert len(prism_patch['shipments']) == 1

        if hint == 'pbmc':
            assert (prism_patch['shipments'][0]['request']) == "R123"

            assert len(prism_patch['participants']) == 2
            assert len(prism_patch['participants'][0]['samples']) == 2
            assert len(prism_patch['participants'][1]['samples']) == 2
            assert sum(len(s["aliquots"]) for p in prism_patch['participants'] for s in p['samples']) == 6

        elif hint == 'plasma':
            assert (prism_patch['shipments'][0]['request']) == "a123"
            assert len(prism_patch['participants']) == 1
            assert len(prism_patch['participants'][0]['samples']) == 1
            assert len(prism_patch['participants'][0]['samples'][0]['aliquots']) == 1

        else: 
            assert False, f'add {hint} specific asserts'

    if hint in SUPPORTED_ASSAYS:
        # olink is different in structure - no array of assays, only one.
        if hint == 'olink':
            prism_patch_assay_records = prism_patch['assays'][hint]['records']
            assert len(prism_patch['assays'][hint]['records']) == 2

        elif hint == 'cytof':
            assert len(prism_patch['assays'][hint]) == 1
            assert 'records' in prism_patch['assays'][hint][0]
            assert len(prism_patch['assays'][hint][0]['records']) == 2
            assert len(prism_patch['assays'][hint][0]['cytof_antibodies']) == 2

        elif hint == 'wes':
            assert len(prism_patch['assays'][hint][0]['records']) == 2

        else:
            raise NotImplementedError(f"no support in test for this hint {hint}")

    for f in file_maps:
        assert f'{hint}/' in f.gs_key, f"No {hint} hint found"

    # And we need set lead_organization_study_id to be the same for testing
    original_ct = copy.deepcopy(TEST_PRISM_TRIAL) 
    if hint in ["olink", "cytof"]:
        original_ct['lead_organization_study_id'] = 'test_prism_trial_id'
        prism_patch['lead_organization_study_id'] = 'test_prism_trial_id'

    # "prismify" provides only a patch so we need to merge it into a "full" ct
    full_after_prism = merge_clinical_trial_metadata(prism_patch, original_ct)

    # Assert we still have a good clinical trial object, so we can save it.
    validator.validate(full_after_prism)

    patch_copy_4_artifacts = copy.deepcopy(prism_patch)

    #now we simulate that upload was successful 
    merged_gs_keys = []
    for i, fmap_entry in enumerate(file_maps):

        # attempt to merge
        patch_copy_4_artifacts, artifact = merge_artifact(
                patch_copy_4_artifacts,
                artifact_uuid=fmap_entry.upload_placeholder,
                object_url=fmap_entry.gs_key,
                assay_type=hint,
                file_size_bytes=i,
                uploaded_timestamp="01/01/2001",
                md5_hash=f"hash_{i}"
            )

        # check that the data_format was set
        assert 'data_format' in artifact

        # assert we still have a good clinical trial object, so we can save it
        validator.validate(merge_clinical_trial_metadata(patch_copy_4_artifacts, original_ct))

        # we will than search for this url in the resulting ct, 
        # to check all artifacts were indeed merged
        merged_gs_keys.append(fmap_entry.gs_key)

    # `merge_artifact` modifies ct in-place, so 
    full_ct = merge_clinical_trial_metadata(patch_copy_4_artifacts, original_ct)

    # validate the full clinical trial object
    validator.validate(full_ct)

    if hint == 'wes':
        assert len(merged_gs_keys) == 3 * 2 # 3 files per entry in xlsx
        assert set(merged_gs_keys) == set(WES_TEMPLATE_EXAMPLE_GS_URLS.keys())

    elif hint == 'olink':
        assert len(merged_gs_keys) == 5 # 2 files per entry in xlsx + 1 file in preamble

    elif hint in SUPPORTED_MANIFESTS:
        assert len(merged_gs_keys) == 0

    elif hint == 'cytof':
        # TODO: This will need ot be updated when we accept a list of source fcs files
        assert len(merged_gs_keys) == 6

    else:
        assert False, f"add {hint} assay specific asserts"

    for file_map_entry in file_maps:
        assert len((full_ct | grep(fmap_entry.gs_key))['matched_values']) == 1 # each gs_url only once

    # olink is special - it's not an array
    if hint == "olink":
        assert len(full_ct['assays'][hint]['records']) == 2, "More records than expected"

    elif hint == 'wes':
        assert len(full_ct['assays'][hint]) == 1+len(TEST_PRISM_TRIAL['assays'][hint]), f"Multiple {hint}-assays created instead of merging into one"
        assert len(full_ct['assays'][hint][0]['records']) == 2, "More records than expected"

    elif hint in SUPPORTED_MANIFESTS:
        assert full_ct["assays"] == original_ct["assays"]

    elif hint == 'cytof':
        assert len(full_ct['assays'][hint]) == 1

    else:
        assert False, f"add {hint} assay specific asserts"


    dd = DeepDiff(full_after_prism, full_ct)

    if hint=='wes':
        # 6 files * 7 artifact atributes
        assert len(dd['dictionary_item_added']) == 6*7, "Unexpected CT changes"

        # nothing else in diff
        assert list(dd.keys()) == ['dictionary_item_added'], "Unexpected CT changes"

    elif hint == "olink":
        assert list(dd.keys()) == ['dictionary_item_added'], "Unexpected CT changes"

        # 7 artifact atributes * 5 files (2 per record + 1 study)
        assert len(dd['dictionary_item_added']) == 7*(2*2+1), "Unexpected CT changes"

    elif hint in SUPPORTED_MANIFESTS:
        
        assert len(dd) == 0, "Unexpected CT changes"

    elif hint == 'cytof':
        assert len(dd['dictionary_item_added']) == 7*6, "Unexpected CT changes"

    else:
        assert False, f"add {hint} assay specific asserts"


def test_merge_stuff():

    obj1 = {'_preamble_obj': 'copy_for:cytof:Antibody Information:row_0', 'cytof_antibodies': [{'_data_obj': 'cytof:Antibody Information:row_0', 'antibody': 'CD8', 'clone': 'C8/144b', 'company': 'DAKO', 'cat_num': 'C8-ABC', 'lot_num': '3983272', 'isotope': '146Nd', 'dilution': '100X', 'stain_type': 'Surface Stain'}]}
    obj2 = {'_preamble_obj': 'copy_for:cytof:Antibody Information:row_1', 'cytof_antibodies': [{'_data_obj': 'cytof:Antibody Information:row_1', 'antibody': 'PD-L1', 'clone': 'C2/11p', 'company': 'DAKO', 'cat_num': 'C8-AB123', 'lot_num': '1231272', 'isotope': '146Nb', 'dilution': '100X', 'stain_type': 'Surface Stain'}]}

    schema = load_and_validate_schema(os.path.join(SCHEMA_DIR, "assays/cytof_assay.json"))
    obj1 = {"pizza": "peperoni", "slices": [{"topping": "123"}]}
    obj2 = {"soda": "934857", "slices": [{"topping": "abc"}]}

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "pizza": {
                "type": "string"
            },
            "mergeStrategy": "objectMerge",
            "allOf": [
                {
                    "soda": {
                        "type": "object",
                        "properties": {
                            "prob": {
                                "type": "number"
                            }
                        }
                    },
                },
                {
                    "slices": {
                        "type": "array",
                        "items": {
                            "properties": {
                                "topping": {
                                    "type": "string"
                                }
                            }
                        },
                        "mergeStrategy": "append"
                    }
                },

            ]
        }
    }

    # this merge will clobber slices because merging across allOf doesn't work
    merger = Merger(schema)
    xyz = merger.merge(obj1, obj2)
    assert len(xyz['slices']) == 1
