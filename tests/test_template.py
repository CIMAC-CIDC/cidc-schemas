# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.template` module."""

import os
import pytest

from cidc_schemas.constants import TEMPLATE_DIR
from cidc_schemas.template import Template, generate_empty_template
from cidc_schemas.prism import SUPPORTED_ASSAYS, SUPPORTED_MANIFESTS, SUPPORTED_TEMPLATES

# NOTE: see conftest.py for pbmc_template and tiny_template fixture definitions


def test_pbmc_loaded(pbmc_template):
    """Smoke test to ensure worksheets loaded from pbmc template"""
    assert 'shipment' in pbmc_template.worksheets
    assert 'aliquots' in pbmc_template.worksheets


def test_tiny_loaded(tiny_template):
    """Smoke test to ensure worksheets loaded from tiny template"""
    assert 'TEST_SHEET' in tiny_template.worksheets


def test_from_type():
    assert 'shipment' in Template.from_type('pbmc').worksheets
    assert 'aliquots' in Template.from_type('pbmc').worksheets
    assert 'WES' in Template.from_type('wes').worksheets

    with pytest.raises(Exception, match='unknown template type'):
        Template.from_type('foo')


def test_worksheet_validation():
    """Check validation errors on invalid worksheets"""

    def check_validation_error(schema, msg):
        with pytest.raises(AssertionError) as e:
            Template._validate_worksheet("", schema)
        assert msg in str(e.value)

    unknown_section = {
        'title': '',
        'properties': {
            'unknown_section_name': []
        }
    }
    check_validation_error(unknown_section, 'unknown worksheet sections')

    # TODO: do we need any other worksheet-level validations?


def test_worksheet_processing():
    """Ensure that worksheet schemas are processed as expected"""
    worksheet = {
        "preamble_rows": {
            # should be converted to lowercase
            "aAa": {}
        },
        "data_columns": {
            # shouldn't be converted to lowercase
            "One": {
                # should be converted to lowercase
                "BbB": {}
            }
        }
    }

    target = {
        "preamble_rows": {
            "aaa": {}
        },
        "data_columns": {
            "One": {
                "bbb": {}
            }
        }
    }

    assert Template._process_worksheet(worksheet) == target


def generate_all_templates(target_dir: str):
    """
    Generate empty template .xlsx files for every available template schema and 
    write them to the target directory.
    """
    # We expect two directories: one for metadata schemas and one for manifests
    for template_type_dir in os.listdir(TEMPLATE_DIR):
        if not template_type_dir.startswith('.'):
            # Create the directory for this template type
            target_subdir = os.path.join(target_dir, template_type_dir)
            if not os.path.exists(target_subdir):
                os.makedirs(target_subdir)


            schema_subdir = os.path.join(TEMPLATE_DIR, template_type_dir)

            # Create a new empty template for each template schema in schema_subdir
            for template_schema_file in os.listdir(schema_subdir):
                # skip non-supported templates
                for x in SUPPORTED_TEMPLATES:
                    if template_schema_file.count(x) > 0:
                        continue
                if not template_schema_file.startswith('.'):
                    schema_path = os.path.join(schema_subdir, template_schema_file)
                    template_xlsx_file = template_schema_file.replace('.json', '.xlsx')
                    target_path = os.path.join(target_subdir, template_xlsx_file)
                    generate_empty_template(schema_path, target_path)


def test_generate_empty_template(pbmc_schema_path, pbmc_template, tmpdir):
    """Check that generate_empty_template generates the correct template."""
    # Generate the xlsx file with the convenience method
    target_path = tmpdir.join('pbmc_target.xlsx')
    generate_empty_template(pbmc_schema_path, target_path)

    # Generate the xlsx file from the known-good Template instance
    # for comparison
    cmp_path = tmpdir.join('pbmc_truth.xlsx')
    pbmc_template.to_excel(cmp_path)

    # Check that the files have the same contents
    with open(target_path, 'rb') as generated, open(cmp_path, 'rb') as comparison:
        assert generated.read() == comparison.read()


def test_generate_all_templates(tmpdir):
    """Check that generate_all_templates appears to, in fact, generate all templates."""
    generate_all_templates(tmpdir)

    # Run twice to ensure we overwrite files without issue
    generate_all_templates(tmpdir)

    # Check that the right number of empty templates was generated
    schema_files = []
    for _, _, fs in os.walk(TEMPLATE_DIR):
        schema_files += [f for f in fs if not f[0] == '.']
    generated_files = [f for _, _, fs in os.walk(tmpdir) for f in fs]
    assert len(schema_files) == len(generated_files)

    # Check that the empty templates have the right names
    generated_filenames = set(f.rstrip('.xlsx') for f in generated_files)
    schema_filenames = set(f.rstrip('.json') for f in schema_files)
    assert generated_filenames == schema_filenames
