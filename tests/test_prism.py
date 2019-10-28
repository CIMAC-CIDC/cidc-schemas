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
from collections import namedtuple
from jsonmerge import Merger
from unittest.mock import MagicMock, patch as mock_patch


from .constants import TEST_DATA_DIR

from cidc_schemas import prism
from cidc_schemas.prism import prismify, merge_artifact, \
    merge_clinical_trial_metadata, InvalidMergeTargetException, \
    SUPPORTED_ASSAYS, SUPPORTED_MANIFESTS, SUPPORTED_TEMPLATES, \
    PROTOCOL_ID_FIELD_NAME, parse_npx, merge_artifact_extra_metadata, \
    PRISM_STRATEGIES, ThrowOnCollision, MergeCollisionException

from cidc_schemas.json_validation import load_and_validate_schema, InDocRefNotFoundError
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader

from .constants import ROOT_DIR, SCHEMA_DIR, TEMPLATE_EXAMPLES_DIR, TEST_DATA_DIR
from .test_templates import template_set
from .test_assays import ARTIFACT_OBJ


def prismify_test_set(filter = None):
    yielded = False

    for template, xlsx_path in template_set():
        if filter and not template.type in filter:
            continue
        xlsx, errors = XlTemplateReader.from_excel(xlsx_path)
        assert not errors
        yield xlsx, template
        yielded = True
    
    if not yielded:
        raise Exception(f"no prismify test for filter {filter!r} found")

TEST_PRISM_TRIAL = {
        PROTOCOL_ID_FIELD_NAME: "test_prism_trial_id",
        "participants": [
            {
                "cimac_participant_id": "CM-TEST-PAR1",
                "participant_id": "TEST-PAR1-03",
                "cohort_name": "Arm_A",
                "samples": [
                    {
                        "aliquots": [
                            {
                                "slide_number": "1",
                                "sample_volume_units": "Other",
                                "material_used": 1,
                                "material_remaining": 0,
                                "quality_of_shipment": "Other",
                                "aliquot_replacement": "N/A",
                                "aliquot_status": "Other"
                            },
                        ],
                        "cimac_id": "CM-TEST-PAR1-11",
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
                        "aliquots": [
                            {
                                "slide_number": "1",
                                "sample_volume_units": "Other",
                                "material_used": 2,
                                "material_remaining": 0,
                                "quality_of_shipment": "Other",
                                "aliquot_replacement": "N/A",
                                "aliquot_status": "Other"
                            }
                        ],
                        "cimac_id": "CM-TEST-PAR1-21",
                        "parent_sample_id": "test_sample_2",
                        "collection_event_name": "Baseline",
                        "sample_location": "---",
                        "type_of_sample": "Other",
                        "type_of_primary_container": "Other",
                    }
                ],
                "cimac_participant_id": "CM-TEST-PAR2",
                "participant_id": "TEST-PAR2-03",
                "cohort_name": "Arm_Z"
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
                            "cimac_id": "CM-TEST-PAR1-11",
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
                            "cimac_id": "CM-TEST-PAR1-21",
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
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]+'/CM-TEST-PAR1-11/wes/r1.fastq': 
    "r1.1",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]+'/CM-TEST-PAR1-11/wes/r2.fastq': 
    "r2.1",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]+'/CM-TEST-PAR1-11/wes/rgm.txt': 
    "read_group_mapping_file.1",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]+'/CM-TEST-PAR1-21/wes/r1.fastq': 
    "r1.2",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]+'/CM-TEST-PAR1-21/wes/r2.fastq': 
    "r2.2",
    TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]+'/CM-TEST-PAR1-21/wes/rgm.txt': 
    "read_group_mapping_file.2"
}


def test_test_data():

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    validator.validate(TEST_PRISM_TRIAL)


def test_merge_core():

    # create aliquot
    aliquot = {
        "slide_number": "12",
        "sample_volume_units": "Other",
        "material_used": 1,
        "material_remaining": 0,
        "quality_of_shipment": "Other",
        "aliquot_replacement": "N/A",
        "aliquot_status": "Other"
    }

    # create the sample.
    sample = {
        "cimac_id": "CM-TRIA-PA12-34",
        "parent_sample_id": "blank",
        "aliquots": [aliquot],
        "collection_event_name": "Baseline",
        "sample_location": "---",
        "type_of_sample": "Other",
        "type_of_primary_container": "Other",
    }

    # create the participant
    participant = {
        "cimac_participant_id": "CM-TEST-PART",
        "participant_id": "blank",
        "samples": [sample],
        "cohort_name": "Arm_Z"
    }

    # create the trial
    ct1 = {
        PROTOCOL_ID_FIELD_NAME: "test",
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
    ct4['participants'][0]['samples'][0]['cimac_id'] = 'new_id_1'

    ct5 = merger.merge(ct3, ct4)
    assert len(ct5['participants'][0]['samples']) == 2

    # now lets add a new aliquot to one of the samples.
    ct6 = copy.deepcopy(ct5)
    aliquot2 = ct6['participants'][0]['samples'][0]['aliquots'][0]
    aliquot2['slide_number'] = 'new_ali_id_1'

    ct7 = merger.merge(ct5, ct6)
    assert len(ct7['participants'][0]['samples'][0]['aliquots']) == 2


MINIMAL_TEST_TRIAL = {
    PROTOCOL_ID_FIELD_NAME: "minimal",
    "participants": [
        {
            "samples": [
                {
                    "aliquots": [
                        {
                            "slide_number": "1",
                            "sample_volume_units": "Other",
                            "material_used": 1,
                            "material_remaining": 0,
                            "quality_of_shipment": "Other",
                            "aliquot_replacement": "N/A",
                            "aliquot_status": "Other"
                        }
                    ],
                    "collection_event_name": "Baseline",
                    "sample_location": "---",
                    "type_of_sample": "Other",
                    "type_of_primary_container": "Other",
                    "parent_sample_id": "test_min_Sample_1",
                    "cimac_id": "CM-TEST-MIN1-01"
                }
            ],
            "cimac_participant_id": "CM-TEST-MIN1",
            "participant_id": "test_min_Patient_1",
            "cohort_name": "Arm_Z"
        }
    ]
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
    a2['participants'][0]['samples'][0]['cimac_id'] = "something different"

    # create validator assert schema is valid.
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # merge them
    merger = Merger(schema)
    a3 = merger.merge(a1, a2)
    assert len(a3['participants']) == 1
    assert len(a3['participants'][0]['samples']) == 2


@pytest.mark.parametrize('xlsx, template', prismify_test_set())
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

    if template.type == 'cytof':
        assert "CYTOF_TEST1" == ct[PROTOCOL_ID_FIELD_NAME]
        ct[PROTOCOL_ID_FIELD_NAME] = 'test_prism_trial_id'

    if template.type == 'ihc':
        assert "ihc_test_trial" == ct[PROTOCOL_ID_FIELD_NAME]
        ct[PROTOCOL_ID_FIELD_NAME] = 'test_prism_trial_id'

    if template.type in SUPPORTED_ASSAYS:
        # olink is different - is will never have array of assay "runs" - only one
        if template.type != 'olink':
            assert len(ct['assays'][template.type]) == 1

    elif template.type in SUPPORTED_MANIFESTS:
        assert not ct.get('assays'), "Assay created during manifest prismify"

    else:
        assert False, f"Unknown template {template.type}"

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema)
    merged = merger.merge(TEST_PRISM_TRIAL, ct)

    # assert works
    errors = list(validator.iter_errors(merged))
    assert not errors 

    if template.type in SUPPORTED_ASSAYS :
        assert merged[PROTOCOL_ID_FIELD_NAME] == "test_prism_trial_id"
    else:
        assert TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME] == merged[PROTOCOL_ID_FIELD_NAME]


@pytest.mark.parametrize('template, xlsx_path', template_set())
def test_unsupported_prismify(template, xlsx_path):

    # skipp supported
    if template.type in SUPPORTED_TEMPLATES:
        return

    with pytest.raises(NotImplementedError):
        prismify(xlsx_path, schema_path)



@pytest.mark.parametrize('xlsx, template', prismify_test_set())
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

    # assert we have the right file counts etc.
    if template.type == "wes":

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
        assert 6 == sum([x.gs_key.startswith(TEST_PRISM_TRIAL[PROTOCOL_ID_FIELD_NAME]) for x in file_maps])

        # all that with
        # 1 trial id
        assert 1 == len(set([x.gs_key.split("/")[0] for x in file_maps]))
        # 2 samples
        assert ['CM-TEST-PAR1-11', 'CM-TEST-PAR1-21'] == list(sorted(set([x.gs_key.split("/")[1] for x in file_maps])))

    elif template.type == 'olink':

        # we should have 2 npx files
        assert 2 == sum([x.gs_key.endswith("assay_npx.xlsx") for x in file_maps])

        # we should have 2 raw_ct files
        assert 2 == sum([x.gs_key.endswith("assay_raw_ct.xlsx") for x in file_maps])

        # 4 assay level + 1 combined in tots
        assert 5 == sum([x.local_path.startswith("olink_assay") for x in file_maps])

        # we should have 1 study level npx
        assert 1 == sum([x.gs_key.endswith("study_npx.xlsx") for x in file_maps])

        # check the number of files - 1 study + 2*(npx + ct raw)
        assert len(file_maps) == 5
        assert 5 == sum([x.gs_key.startswith("test_prism_trial_id") for x in file_maps])


    elif template.type == 'cytof':
        # TODO: UPdate this to assert we can handle multiple source fcs files

        for x in file_maps:
            assert x.gs_key.endswith(".fcs")
        assert len(file_maps) == 6

    elif template.type == 'ihc':
        assert 2 == sum([x.gs_key.endswith(".tiff") for x in file_maps])


    elif template.type in SUPPORTED_MANIFESTS:

        assert len(file_maps) == 0

    else:
        assert False, f"add {template.type} assay specific asserts"



@pytest.mark.parametrize('xlsx, template', prismify_test_set('cytof'))
def test_prismify_cytof_only(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    ct, file_maps, errs = prismify(xlsx, template, verb=False)
    assert len(errs) == 0

    # we should have 3 files, the processed fcs and two source fcs X2
    assert len(file_maps) == 6

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema)
    merged = merger.merge(TEST_PRISM_TRIAL, ct)

    # assert works
    validator.validate(merged)

@pytest.mark.parametrize('xlsx, template', prismify_test_set('ihc'))
def test_prismify_ihc(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    ct, file_maps, errs = prismify(xlsx, template)

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema)
    merged = merger.merge(TEST_PRISM_TRIAL, ct)

    # assert works
    validator.validate(merged)


@pytest.mark.parametrize('xlsx, template', prismify_test_set('plasma'))
def test_prismify_plasma(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    # parse the spreadsheet and get the file maps
    md_patch, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0
    validator.validate(md_patch)

    assert file_maps == []
    assert 2 == len(md_patch["participants"])
    assert 3 == len(md_patch["participants"][0]["samples"])
    assert md_patch["participants"][0]["samples"][0]["cimac_id"][:-3] == \
        md_patch["participants"][0]["cimac_participant_id"]

    assert md_patch["participants"][0]["gender"]        # filled from 1 tab
    assert md_patch["participants"][0]["cohort_name"]   # filled from another

    assert md_patch["participants"][0]["samples"][0]["processed_sample_id"] # filled from 1 tab
    assert md_patch["participants"][0]["samples"][0]["topography_code"]     # filled from the second tab
    assert md_patch["participants"][0]["samples"][0]["site_description"]    # filled from the second tab


@pytest.mark.parametrize('xlsx, template', prismify_test_set('wes'))
def test_prismify_wes_only(xlsx, template):

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # parse the spreadsheet and get the file maps
    md_patch, file_maps, errs = prismify(xlsx, template)
    assert len(errs) == 0

    for e in validator.iter_errors(md_patch):
        assert isinstance(e, InDocRefNotFoundError) or ("'participants'" in str(e) and "required" in str(e))

    # we merge it with a preexisting one
    # 1. we get all 'required' fields from this preexisting
    # 2. we can check it didn't overwrite anything crucial
    merger = Merger(schema)
    merged = merger.merge(TEST_PRISM_TRIAL, md_patch)

    # assert works
    validator.validate(merged)

    merged_wo_needed_participants = copy.deepcopy(merged)
    merged_wo_needed_participants['participants'][0]['samples'][0]['cimac_id'] = "CM-TEST-NAAA-DA"

    # assert in_doc_ref constraints work
    with pytest.raises(InDocRefNotFoundError):
        validator.validate(merged_wo_needed_participants)

    # 2 record = 2 missing aliquot refs = 2 errors
    assert 2 == len(list(validator.iter_errors(merged_wo_needed_participants)))


@pytest.mark.parametrize('xlsx, template', prismify_test_set('olink'))
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
    merger = Merger(schema)
    merged = merger.merge(MINIMAL_TEST_TRIAL, ct)

    # assert works
    validator.validate(merged)

    # return these for use in other tests
    return ct, file_maps
    
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
        ct, artifact, patch_metadata = merge_artifact(
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
    patch = copy.deepcopy(TEST_PRISM_TRIAL)
    target = copy.deepcopy(TEST_PRISM_TRIAL)

    # first test the fact that base doc must be valid
    del target['participants']
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
    patch['trial_name'] = 'name ABC'
    target['nci_id'] = 'xyz1234'

    ct_merge, errs = merge_clinical_trial_metadata(patch, target)
    assert not errs
    assert ct_merge['trial_name'] == 'name ABC'
    assert ct_merge['nci_id'] == 'xyz1234'

    # updates aren't allowed
    patch['trial_name'] = 'name ABC'
    target['trial_name'] = 'CBA eman'
    with pytest.raises(MergeCollisionException, match="conflicting values for trial_name"):
        merge_clinical_trial_metadata(patch, target)
    target['trial_name'] = patch['trial_name']

    # now change the participant ids
    # this should cause the merge to have two
    # participants.
    patch['participants'][0]['cimac_participant_id'] = 'CM-TEST-DIF1'
    for i, sample in enumerate(patch['participants'][0]['samples']):
        sample['cimac_id'] = f'CM-TEST-DIF1-D{i}'

    ct_merge, errs = merge_clinical_trial_metadata(patch, target)
    assert not errs
    assert len(ct_merge['participants']) == 1+len(TEST_PRISM_TRIAL['participants'])

    # now lets have the same participant but adding multiple samples.
    patch[PROTOCOL_ID_FIELD_NAME] = target[PROTOCOL_ID_FIELD_NAME] 
    patch['participants'][0]['cimac_participant_id'] = \
        target['participants'][0]['cimac_participant_id']
    patch['participants'][0]['samples'][0]['cimac_id'] = 'CM-TEST-PAR1-N1'
    patch['participants'][1]['samples'][0]['cimac_id'] = 'CM-TEST-PAR1-N2'
 
    ct_merge, errs = merge_clinical_trial_metadata(patch, target)
    assert not errs
    assert len(ct_merge['participants']) == len(TEST_PRISM_TRIAL['participants'])
    assert sum(len(p['samples']) for p in ct_merge['participants']) == 2+sum(len(p['samples']) for p in TEST_PRISM_TRIAL['participants'])


@pytest.mark.parametrize('xlsx, template', prismify_test_set())
def test_end_to_end_prismify_merge_artifact_merge(xlsx, template):


    # TODO: implement other assays
    if template.type not in SUPPORTED_TEMPLATES:
        return 

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    # parse the spreadsheet and get the file maps
    prism_patch, file_maps, errs = prismify(xlsx, template, verb=True)
    assert len(errs) == 0

    if template.type in SUPPORTED_MANIFESTS:
        assert len(prism_patch['shipments']) == 1
        
        assert prism_patch['participants'][0]['samples'][0]["cimac_id"].split("-")[:3] == \
            prism_patch['participants'][0]['cimac_participant_id'].split("-")

        if template.type == 'pbmc':
            assert (prism_patch['shipments'][0]['manifest_id']) == "TEST123_pbmc"

            assert len(prism_patch['participants']) == 2
            assert len(prism_patch['participants'][0]['samples']) == 3
            assert len(prism_patch['participants'][1]['samples']) == 3

        elif template.type == 'plasma':
            assert (prism_patch['shipments'][0]['manifest_id']) == "TEST123_plasma"
            assert len(prism_patch['participants']) == 2
            assert len(prism_patch['participants'][0]['samples']) == 3
            assert 'aliquots' not in prism_patch['participants'][0]['samples'][0]

        else: 
            assert False, f'add {template.type} specific asserts'

    if template.type in SUPPORTED_ASSAYS:
        # olink is different in structure - no array of assays, only one.
        if template.type == 'olink':
            prism_patch_assay_records = prism_patch['assays'][template.type]['records']
            assert len(prism_patch['assays'][template.type]['records']) == 2

        elif template.type == 'cytof':
            assert len(prism_patch['assays'][template.type]) == 1
            assert 'records' in prism_patch['assays'][template.type][0]
            assert len(prism_patch['assays'][template.type][0]['records']) == 2
            assert len(prism_patch['assays'][template.type][0]['cytof_antibodies']) == 2

        elif template.type == 'wes':
            assert len(prism_patch['assays'][template.type][0]['records']) == 2

        elif template.type =='ihc':
            assert len(prism_patch['assays'][template.type][0]['records']) == 1

        else:
            raise NotImplementedError(f"no support in test for this template.type {template.type}")

    for f in file_maps:
        assert f'{template.type}/' in f.gs_key, f"No {template.type} template.type found"

    # And we need set PROTOCOL_ID_FIELD_NAME to be the same for testing
    original_ct = copy.deepcopy(TEST_PRISM_TRIAL) 

    # so we can merge
    original_ct[PROTOCOL_ID_FIELD_NAME] = prism_patch[PROTOCOL_ID_FIELD_NAME]
    
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
                md5_hash=f"hash_{i}"
            )

        # check that the data_format was set
        assert 'data_format' in artifact

        # assert we still have a good clinical trial object, so we can save it
        step_ct, errs = merge_clinical_trial_metadata(patch_copy_4_artifacts, original_ct)
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

    if template.type == 'ihc':
        assert len(merged_gs_keys) == 2

    elif template.type == 'wes':
        assert len(merged_gs_keys) == 3 * 2 # 3 files per entry in xlsx
        assert set(merged_gs_keys) == set(WES_TEMPLATE_EXAMPLE_GS_URLS.keys())

    elif template.type == 'olink':
        assert len(merged_gs_keys) == 5 # 2 files per entry in xlsx + 1 file in preamble

    elif template.type in SUPPORTED_MANIFESTS:
        assert len(merged_gs_keys) == 0

    elif template.type == 'cytof':
        # TODO: This will need ot be updated when we accept a list of source fcs files
        assert len(merged_gs_keys) == 6

    else:
        assert False, f"add {template.type} assay specific asserts"

    for file_map_entry in file_maps:
        assert len((full_ct | grep(fmap_entry.gs_key))['matched_values']) == 1 # each gs_url only once

    # olink is special - it's not an array
    if template.type == "olink":
        assert len(full_ct['assays'][template.type]['records']) == 2, "More records than expected"

    elif template.type == 'wes':
        assert len(full_ct['assays'][template.type]) == 1+len(TEST_PRISM_TRIAL['assays'][template.type]), f"Multiple {template.type}-assays created instead of merging into one"
        assert len(full_ct['assays'][template.type][0]['records']) == 2, "More records than expected"

    elif template.type == 'ihc':
        assert len(full_ct['assays'][template.type][0]['records']) == 1, "More records than expected"

    elif template.type in SUPPORTED_MANIFESTS:
        assert full_ct["assays"] == original_ct["assays"]

    elif template.type == 'cytof':
        assert len(full_ct['assays'][template.type]) == 1

    else:
        assert False, f"add {template.type} assay specific asserts"

    dd = DeepDiff(full_after_prism, full_ct)

    if template.type=='wes':

        # 6 files * 7 artifact attributes
        assert len(dd['dictionary_item_added']) == 6*7, "Unexpected CT changes"

        # nothing else in diff
        assert list(dd.keys()) == ['dictionary_item_added'], "Unexpected CT changes"

    elif template.type == 'ihc':
        # 2 files * 7 artifact attributes
        assert len(dd['dictionary_item_added']) == 2*7, "Unexpected CT changes"

    elif template.type == "olink":

        assert list(dd.keys()) == ['dictionary_item_added'], "Unexpected CT changes"

        # 7 artifact attributes * 5 files (2 per record + 1 study)
        assert len(dd['dictionary_item_added']) == 7*(2*2+1), "Unexpected CT changes"

    elif template.type in SUPPORTED_MANIFESTS:
        assert len(dd) == 0, "Unexpected CT changes"

    elif template.type == 'cytof':
        assert len(dd['dictionary_item_added']) == 7*6, "Unexpected CT changes"

    else:
        assert False, f"add {template.type} assay specific asserts"


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


def test_prism_joining_tabs(monkeypatch):
    """ Tests whether prism can join data from two excel tabs for a shared metadata subtree """

    load_workbook = MagicMock(name="load_workbook")
    monkeypatch.setattr("openpyxl.load_workbook", load_workbook)
    workbook = load_workbook.return_value = MagicMock(name="workbook")
    wb= {"participants": MagicMock(name="participants"), "samples": MagicMock(name="samples"), }
    workbook.__getitem__.side_effect = wb.__getitem__
    workbook.sheetnames = wb.keys()
    cell = namedtuple("cell", ["value"])
    wb["participants"].iter_rows.return_value = [
        map(cell, ["#h", "PA id", "PA prop"]),
        map(cell, ["#d", "CM-PA0",  "0"]),
        map(cell, ["#d", "CM-PA1",  "1"]),
    ]
    wb["samples"].iter_rows.return_value = [
        map(cell, ["#h", "SA_id",   "SA_prop"]),
        map(cell, ["#d", "CM-PA1-SA0",  "100"]),
        map(cell, ["#d", "CM-PA1-SA1",  "101"]),
        map(cell, ["#d", "CM-PA0-SA0",  "000"]),
        map(cell, ["#d", "CM-PA0-SA1",  "001"]),
    ]

    template = Template({
        "$id": "test_ship",
        "title": "participants and shipment",
        "properties": {
            "worksheets": {
                "participants": {
                    "prism_preamble_object_schema" : "clinical_trial.json",
                    "prism_preamble_object_pointer" : "#",
                    "prism_data_object_pointer" : "/participants/0/samples/0",
                    "preamble_rows": {
                    },
                    "data_columns": {
                        "Samples": {
                            "PA id": {
                                "merge_pointer": "2/cimac_participant_id",
                                "type_ref": "participant.json#properties/cimac_participant_id"
                            },
                            "PA prop": {
                              "merge_pointer": "0/participant_id",
                              "type_ref": "participant.json#properties/participant_id"
                            }
                        }
                    }
                },
                "samples": {
                    "prism_preamble_object_schema" : "clinical_trial.json",
                    "prism_preamble_object_pointer" : "#",
                    "prism_data_object_pointer" : "/participants/0/samples/0",
                    "preamble_rows": {
                    },
                    "data_columns": {
                        "Samples": {
                            "SA_id": {
                                "merge_pointer": "/cimac_id",
                                "type_ref": "sample.json#properties/cimac_id",
                                "process_as": [{
                                  "merge_pointer": "2/cimac_participant_id",
                                  "parse_through": "lambda x: '-'.join(x.split('-')[:2])"
                                }]
                            },
                            "SA_prop": {
                              "merge_pointer": "0/parent_sample_id",
                              "type_ref": "sample.json#properties/parent_sample_id"
                            }

                        }
                    }
                }

            }
        }
    }, "test_prism_joining_tabs")

    monkeypatch.setattr("cidc_schemas.prism.SUPPORTED_TEMPLATES", ["test_prism_joining_tabs"])

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    patch, file_maps, errs = prismify(xlsx, template, verb=False)
    assert len(errs) == 0

    assert 2 == len(patch["participants"])
    
    assert "CM-PA0" == patch["participants"][0]["cimac_participant_id"]
    assert 2 == len(patch["participants"][0]["samples"])
    
    assert "CM-PA0-SA0"  == patch["participants"][0]["samples"][0]["cimac_id"]
    assert "000"  == patch["participants"][0]["samples"][0]["parent_sample_id"]

    assert "CM-PA0-SA1"  == patch["participants"][0]["samples"][1]["cimac_id"]
    assert "001"  == patch["participants"][0]["samples"][1]["parent_sample_id"]
    
    assert "CM-PA1" == patch["participants"][1]["cimac_participant_id"]
    assert 2 == len(patch["participants"][1]["samples"])

    assert 0 == len(file_maps)
    
@pytest.fixture
def npx_file_path():
    return os.path.join(TEST_DATA_DIR, 'olink', 'olink_assay_1_NPX.xlsx')

@pytest.fixture
def npx_combined_file_path():
    return os.path.join(TEST_DATA_DIR, 'olink', 'olink_assay_combined.xlsx')


def test_merge_extra_metadata_olink(npx_file_path, npx_combined_file_path):
    xlsx, template = list(prismify_test_set('olink'))[0]
    ct, file_infos = test_prismify_olink_only(xlsx, template)

    for finfo in file_infos:
        if finfo.metadata_availability:
            if 'combined' in finfo.local_path:
                local_path = npx_combined_file_path
            else:
                local_path = npx_file_path

            with open(local_path, 'rb') as npx_file:
                merge_artifact_extra_metadata(ct, finfo.upload_placeholder, 'olink', npx_file)

    study = ct['assays']['olink']['study']
    files = ct['assays']['olink']['records'][0]['files']

    assert set(files['assay_npx']['samples']) == {'CM-TEST-PA01-A1', 'CM-TEST-PA02-A1', 'CM-TEST-PA03-A1', 'CM-TEST-PA04-A1'}
    assert set(study['study_npx']['samples']) == {'CM-TEST-PA01-A1', 'CM-TEST-PA02-A1', 'CM-TEST-PA03-A1', 'CM-TEST-PA04-A1', 'CM-TEST-PA05-A1', 'CM-TEST-PA06-A1', 'CM-TEST-PA07-A1', 'CM-TEST-PA08-A1', 'CM-TEST-PA09-A1'}


def test_parse_npx_invalid(npx_file_path):
    # test the parse function by passing a file path
    with pytest.raises(TypeError):
        samples = parse_npx(npx_file_path)


def test_parse_npx_single(npx_file_path):
    # test the parse function
    f = open(npx_file_path, 'rb')
    samples = parse_npx(f)

    assert samples["number_of_samples"] == 4
    assert set(samples["samples"]) == {'CM-TEST-PA01-A1', 'CM-TEST-PA02-A1', 'CM-TEST-PA03-A1', 'CM-TEST-PA04-A1'}


def test_parse_npx_merged(npx_combined_file_path):
    # test the parse function
    f = open(npx_combined_file_path, 'rb')
    samples = parse_npx(f)

    assert samples["number_of_samples"] == 9
    assert set(samples["samples"]) == {'CM-TEST-PA01-A1', 'CM-TEST-PA02-A1', 'CM-TEST-PA03-A1', 'CM-TEST-PA04-A1', 'CM-TEST-PA05-A1', 'CM-TEST-PA06-A1', 'CM-TEST-PA07-A1', 'CM-TEST-PA08-A1', 'CM-TEST-PA09-A1'}

def test_throw_on_collision():
    """Test the custom ThrowOnCollision merge strategy"""
    schema = {
        "type": "object",
        "properties": {
            "l": {
                "type": "array",
                "items": {
                    "cimac_id": {
                        "type": "string",
                    }, 
                    "a": {
                        "type": "integer"
                    }
                },
                "mergeStrategy": "arrayMergeById",
                "mergeOptions": {
                    "idRef": "/cimac_id"
                }
            }
        }
    }

    merger = Merger(schema, strategies=PRISM_STRATEGIES)

    # Identical values, no collision - no error
    base = {'l': [{'cimac_id': 'c1', 'a': 1}]}
    assert merger.merge(base, base)

    # Different values, collision - error
    head = {'l': [{'cimac_id': 'c1', 'a': 2}]}
    with pytest.raises(MergeCollisionException, match="1 \(current\) != 2 \(incoming\)"):
        merger.merge(base, head)

    # Some identical and some different values - no error, proper merge
    base['l'].append({'cimac_id': 'c2', 'a': 2})
    head = {'l': [base['l'][0], {'cimac_id': 'c3', 'a': 3}]}
    assert merger.merge(base, head) == {'l': [*base['l'], head['l'][-1]]}
    
