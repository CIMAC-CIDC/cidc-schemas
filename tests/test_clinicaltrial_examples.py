#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for data model schemas."""

import os
import pytest
import json
import jsonschema

from cidc_schemas.json_validation import load_and_validate_schema


def example_paths():
    """Get the path to every .json in the 'data/clinicaltrial_examples' directory"""
    for root, _, paths in os.walk(
        os.path.join(os.path.dirname(__file__), "data/clinicaltrial_examples")
    ):
        for path in paths:
            if not path.endswith(".json"):
                continue

            yield root, path


@pytest.mark.parametrize("example_path", example_paths(), ids=lambda x: x[1])
def test_schema(example_path):
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)

    full_path = os.path.join(*example_path)
    _, fname = example_path

    with open(full_path) as file:
        try:
            ct_example = json.load(file)
        except Exception as e:
            raise Exception(f"Error decoding {example_path}: {e}")

        try:
            validator.validate(ct_example)
        except jsonschema.exceptions.ValidationError as e:
            raise Exception(
                f'Failed to validate {fname}:{"["+"][".join(repr(p) for p in e.absolute_path)+"]"} \
                \n {e.message} \
                \n CT_SCHEMA{"["+"][".join(repr(p) for p in e.absolute_schema_path)+"]"} \
                \n instance {e.instance}'
            )


{
    "records": [
        {
            "chip_barcode": "1111",
            "files": {
                "assay_npx": {
                    "upload_placeholder": "7c5afba4-5478-49ed-bd1c-8b39a9829401",
                    "facet_group": "/olink/batch_/chip_/assay_npx.xlsx",
                },
                "assay_raw_ct": {
                    "upload_placeholder": "80eff6f3-2e75-473a-b005-2decc6430cd9",
                    "facet_group": "/olink/batch_/chip_/assay_raw_ct.csv",
                },
            },
            "run_date": "2019-12-12 00:00:00",
            "run_time": "10:11:00",
            "instrument": "MIOMARKHD411",
            "fludigm_application_version": "4.1.3",
            "fludigm_application_build": "20140305.43",
            "probe_type": "FAM-MGB",
            "passive_reference": "ROX",
            "quality_threshold": 0.5,
            "baseline_correction": "Linear",
            "number_of_samples": 90.0,
            "number_of_samples_failed": 5.0,
            "npx_manager_version": "Olink NPX Manager 0.0.82.0",
        },
        {
            "chip_barcode": "1112",
            "files": {
                "assay_npx": {
                    "upload_placeholder": "fb214d49-469d-4c74-9e52-6da4d78570f9",
                    "facet_group": "/olink/batch_/chip_/assay_npx.xlsx",
                },
                "assay_raw_ct": {
                    "upload_placeholder": "8c60dd6a-597b-4222-8e72-80d308fe4653",
                    "facet_group": "/olink/batch_/chip_/assay_raw_ct.csv",
                },
            },
            "run_date": "2019-12-12 00:00:00",
            "run_time": "10:11:00",
            "instrument": "MIOMARKHD411",
            "fludigm_application_version": "4.1.3",
            "fludigm_application_build": "20140305.43",
            "probe_type": "FAM-MGB",
            "passive_reference": "ROX",
            "quality_threshold": 0.5,
            "baseline_correction": "Linear",
            "number_of_samples": 80.0,
            "number_of_samples_failed": 10.0,
            "npx_manager_version": "Olink NPX Manager 0.0.82.0",
        },
    ]
}
