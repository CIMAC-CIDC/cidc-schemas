#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for PRISM the module which pulls JSON objects from excel spreadsheets."""

import os
import copy
import pytest
import jsonschema
import json
from deepdiff import grep
from pprint import pprint
from jsonmerge import Merger

from cidc_schemas.prism import prismify, merge_artifact, \
    merge_clinical_trial_metadata
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
                                "assay": {
                                    "wes": {
                                        "assay_creator": "Mount Sinai",
                                        "assay_category": "Whole Exome Sequencing (WES)",
                                        "enrichment_vendor_kit": "Twist",
                                        "library_vendor_kit": "KAPA - Hyper Prep",
                                        "sequencer_platform": "Illumina - NextSeq 550",
                                        "paired_end_reads": "Paired",
                                        "read_length": 100,
                                        "records": [
                                            {
                                                "library_kit_lot": "lot abc",
                                                "enrichment_vendor_lot": "lot 123",
                                                "library_prep_date": "2019-05-01 00:00:00",
                                                "capture_date": "2019-05-02 00:00:00",
                                                "input_ng": 100,
                                                "library_yield_ng": 700,
                                                "average_insert_size": 250,
                                                "entry_id": "abc1"
                                            }
                                        ]
                                    }
                                },
                                "cimac_aliquot_id": "aliquot 1"
                            },
                        ],
                        "cimac_sample_id": "sample 1",
                        "genomic_source": "Tumor"
                    },
                    {
                        "aliquots": [
                            {
                                "assay": {
                                    "wes": {
                                        "assay_creator": "Mount Sinai",
                                        "assay_category": "Whole Exome Sequencing (WES)",
                                        "enrichment_vendor_kit": "Twist",
                                        "library_vendor_kit": "KAPA - Hyper Prep",
                                        "sequencer_platform": "Illumina - NextSeq 550",
                                        "paired_end_reads": "Paired",
                                        "read_length": 100,
                                        "records": [
                                            {
                                                "library_kit_lot": "lot abc",
                                                "enrichment_vendor_lot": "lot 123",
                                                "library_prep_date": "2019-05-01 00:00:00",
                                                "capture_date": "2019-05-02 00:00:00",
                                                "input_ng": 100,
                                                "library_yield_ng": 700,
                                                "average_insert_size": 250,
                                                "entry_id": "abc2"
                                            }
                                        ]
                                    }
                                },
                                "cimac_aliquot_id": "aliquot 2"
                            }
                        ],
                        "cimac_sample_id": "sample 2",
                        "genomic_source": "Normal"
                    }
                ],
                "cimac_participant_id": "patient 1"
            }
        ]
    }


def test_merge_core():

    # create aliquot
    aliquot = {
        "cimac_aliquot_id": "1234"
    }

    # create the sample.
    sample = {
        "cimac_sample_id": "S1234",
        "site_sample_id": "blank",
        "aliquots": [aliquot]
    }

    # create the participant
    participant = {
        "cimac_participant_id": "P1234",
        "trial_participant_id": "blank",
        "samples": [sample]
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


def test_assay_merge():

    # two wes assays.
    a1 = {
        "lead_organization_study_id": "10021",
        "participants": [
            {
                "samples": [
                    {
                        "genomic_source": "Tumor",
                        "aliquots": [
                            {
                                "assay": {
                                    "wes": {
                                        "assay_creator": "Mount Sinai",
                                        "assay_category": "Whole Exome Sequencing (WES)",
                                        "enrichment_vendor_kit": "Twist",
                                        "library_vendor_kit": "KAPA - Hyper Prep",
                                        "sequencer_platform": "Illumina - NextSeq 550",
                                        "paired_end_reads": "Paired",
                                        "read_length": 100,
                                        "records": [
                                            {
                                                "library_kit_lot": "lot abc",
                                                "enrichment_vendor_lot": "lot 123",
                                                "library_prep_date": "2019-05-01 00:00:00",
                                                "capture_date": "2019-05-02 00:00:00",
                                                "input_ng": 100,
                                                "library_yield_ng": 700,
                                                "average_insert_size": 250,
                                                "entry_id": "abc"
                                            }
                                        ],
                                    }
                                },
                                "cimac_aliquot_id": "Aliquot 1"
                            }
                        ],
                        "cimac_sample_id": "Sample 1"
                    }
                ],
                "cimac_participant_id": "Patient 1"
            }
        ]
    }
    
    # create a2 and modify ids to trigger merge behavior
    a2 = copy.deepcopy(a1)
    a2['participants'][0]['samples'][0]['cimac_sample_id'] = "something different"

    # create validator assert schemas are valid.
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # merge them
    merger = Merger(schema)
    a3 = merger.merge(a1, a2)
    assert len(a3['participants']) == 1
    assert len(a3['participants'])


def test_prism():

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # get a specifc template
    for temp_path, xlsx_path in template_paths():

        # extract hint.
        hint = temp_path.split("/")[-1].replace("_template.json", "")

        # TODO: only implemented WES parsing...
        if hint != "wes":
            continue

        # turn into object.
        ct, file_maps = prismify(xlsx_path, temp_path, assay_hint=hint)

        # assert works
        validator.validate(ct)


def test_filepath_gen():

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # get a specifc template
    for temp_path, xlsx_path in template_paths():

        # extract hint.
        hint = temp_path.split("/")[-1].replace("_template.json", "")

        # TODO: only implemented WES parsing...
        if hint != "wes":
            continue

        # parse the spreadsheet and get the file maps
        ct, file_maps = prismify(xlsx_path, temp_path, assay_hint=hint)

        # assert we have the right counts.
        if hint == "wes":

            # check the number of files present.
            assert len(file_maps) == 6

            # we should have 2 fastq per sample.
            assert 4 == sum([1 for x in file_maps if x['gs_key'].count("fastq") > 0])

            # we should have 2 tot forward.
            assert 2 == sum([1 for x in file_maps if x['gs_key'].count("forward") > 0])
            assert 2 == sum([1 for x in file_maps if x['gs_key'].count("reverse") > 0])

            # we should have 2 text files
            assert 2 == sum([1 for x in file_maps if x['gs_key'].count("txt") > 0])

        # assert works
        validator.validate(ct)


def test_wes():

    # create validators
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    schema = validator.schema

    # create the example template.
    temp_path = os.path.join(SCHEMA_DIR, 'templates', 'metadata', 'wes_template.json')
    xlsx_path = os.path.join(TEMPLATE_EXAMPLES_DIR, "wes_template.xlsx")
    hint = 'wes'

    # parse the spreadsheet and get the file maps
    ct, file_maps = prismify(xlsx_path, temp_path, assay_hint=hint)

    # assert works
    validator.validate(ct)


def test_snippet_wes():

    # create the clinical trial.
    ct = copy.deepcopy(CLINICAL_TRIAL)

    # define list of gs_urls.
    urls = [
        '10021/Patient 1/sample 1/aliquot 1/wes_forward.fastq',
        '10021/Patient 1/sample 1/aliquot 1/wes_reverse.fastq',
        '10021/Patient 1/sample 1/aliquot 1/wes_read_group.txt',
        '10021/Patient 1/sample 1/aliquot 2/wes_forward.fastq',
        '10021/Patient 1/sample 1/aliquot 2/wes_reverse.fastq',
        '10021/Patient 1/sample 1/aliquot 2/wes_read_group.txt'
    ]

    # create validator
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    # loop over each url
    searched_urls = []
    for gs_url in urls:

        # attempt to merge
        ct = merge_artifact(
                ct,
                object_url=gs_url,
                file_size_bytes=14,
                uploaded_timestamp="01/01/2001",
                md5_hash="hash1234"
            )

        # assert we stull have a good clinical trial object.
        validator.validate(ct)

        # search for this url and all previous (no clobber)
        searched_urls.append(gs_url)
        for url in searched_urls:
            ds = ct | grep(url)
            assert 'matched_values' in ds
            assert len(ds['matched_values']) > 0


def test_merge_ct_meta():
    """ 
    tests merging of two clinical trial metadata
    objects. Currently this test only supports
    WES but other tests should be added in the
    future
    """

    # create two clinical trials
    ct1 = copy.deepcopy(CLINICAL_TRIAL)
    ct2 = copy.deepcopy(CLINICAL_TRIAL)

    # first test the fact that both snippets must be valid
    del ct1['lead_organization_study_id']
    with pytest.raises(jsonschema.ValidationError):
        merge_clinical_trial_metadata(ct1, ct2)

    with pytest.raises(jsonschema.ValidationError):
        merge_clinical_trial_metadata(ct1, {})

    # next assert the merge is only happening on the same trial
    ct1["lead_organization_study_id"] = "not_the_same"
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
    assert len(ct_merge['participants']) == 2

    # now lets have the same participant but adding multiple samples.
    ct1["lead_organization_study_id"] = ct2["lead_organization_study_id"] 
    ct1['participants'][0]['cimac_participant_id'] = \
        ct2['participants'][0]['cimac_participant_id']
    ct1['participants'][0]['samples'][0]['cimac_sample_id'] = 'new_id_1'
    ct1['participants'][0]['samples'][1]['cimac_sample_id'] = 'new_id_2'

    ct_merge = merge_clinical_trial_metadata(ct1, ct2)
    assert len(ct_merge['participants']) == 1
    assert len(ct_merge['participants'][0]['samples']) == 4
