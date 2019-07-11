#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for PRISM the module which pulls JSON objects from excel spreadsheets."""

import os
import copy
import pytest
import jsonschema
import json
from jsonmerge import Merger

from cidc_schemas.prism import prismify
from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.template import Template
from cidc_schemas.template_writer import RowType
from cidc_schemas.template_reader import XlTemplateReader

from .constants import ROOT_DIR, SCHEMA_DIR, TEMPLATE_EXAMPLES_DIR


def template_paths():
    """
    Get the path to every template schema in the schemas/templates directory
    and their corresponding xlsx example file. 
    """
    template_schema_dir = os.path.join(SCHEMA_DIR, 'templates')

    template_paths = []

    # Collect template schemas
    for root, _, files in os.walk(template_schema_dir):
        for f in files:
            template_paths.append(os.path.join(root, f))

    # Collect template xlsx examples
    for i, schema_path in enumerate(template_paths):
        name = os.path.basename(schema_path).rsplit('.', 1)[0]
        xlsx = f'{name}.xlsx'
        xlsx_path = os.path.join(TEMPLATE_EXAMPLES_DIR, xlsx)
        template_paths[i] = (schema_path, xlsx_path)

    return template_paths


def _fetch_validator(name):

    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "%s.json" % name)
    schema = load_and_validate_schema(schema_path, schema_root)

    # create validator assert schemas are valid.
    return jsonschema.Draft7Validator(schema), schema


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
    validator, schema = _fetch_validator("clinical_trial")
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
    #print(json.dumps(ct5))
    #assert False
    assert len(ct5['participants'][0]['samples']) == 2

    # now lets add a new aliquot to one of the samples.
    ct6 = copy.deepcopy(ct5)
    aliquot2 = ct6['participants'][0]['samples'][0]['aliquots'][0]
    aliquot2['cimac_aliquot_id'] = 'new_ali_id_1'

    ct7 = merger.merge(ct5, ct6)
    assert len(ct7['participants'][0]['samples'][0]['aliquots']) == 2


def test_prism():

    # get a specifc template
    for x, y in template_paths():
        if x.count("wes_template") > 0:
            temp_path = x
            xlsx_path = y

    # turn into object.
    ct = prismify(xlsx_path, temp_path)

    # create validator assert schemas are valid.
    validator, schema = _fetch_validator("clinical_trial")
    validator.validate(ct)