# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.template` module."""

import os
import pytest

from cidc_schemas.constants import TEMPLATE_DIR
from cidc_schemas.template import (
    Template,
    generate_empty_template,
    generate_all_templates,
)

# NOTE: see conftest.py for pbmc_template and tiny_template fixture definitions


def test_pbmc_loaded(pbmc_template):
    """Smoke test to ensure worksheets loaded from pbmc template"""
    assert "Shipment" in pbmc_template.worksheets
    assert "Samples" in pbmc_template.worksheets
    assert "Essential Patient Data" in pbmc_template.worksheets


def test_tiny_loaded(tiny_template):
    """Smoke test to ensure worksheets loaded from tiny template"""
    assert "TEST_SHEET" in tiny_template.worksheets


def test_from_type():
    assert "Shipment" in Template.from_type("pbmc").worksheets
    assert "Samples" in Template.from_type("pbmc").worksheets
    assert "WES" in Template.from_type("wes_fastq").worksheets

    with pytest.raises(Exception, match="unknown template type"):
        Template.from_type("foo")


def test_worksheet_validation():
    """Check validation errors on invalid worksheets"""

    def check_validation_error(schema, msg):
        with pytest.raises(AssertionError) as e:
            Template._validate_worksheet("", schema)
        assert msg in str(e.value)

    unknown_section = {"title": "", "properties": {"unknown_section_name": []}}
    check_validation_error(unknown_section, "unknown worksheet sections")

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
        },
    }

    target = {"preamble_rows": {"aaa": {}}, "data_columns": {"One": {"bbb": {}}}}

    assert Template._process_worksheet(worksheet) == target


def test_generate_empty_template(pbmc_schema_path, pbmc_template, tmpdir):
    """Check that generate_empty_template generates the correct template."""
    # Generate the xlsx file with the convenience method
    target_path = tmpdir.join("pbmc_target.xlsx")
    generate_empty_template(pbmc_schema_path, target_path)

    # Generate the xlsx file from the known-good Template instance
    # for comparison
    cmp_path = tmpdir.join("pbmc_truth.xlsx")
    pbmc_template.to_excel(cmp_path)

    # Check that the files have the same contents
    with open(target_path, "rb") as generated, open(cmp_path, "rb") as comparison:
        assert generated.read() == comparison.read()


def test_generate_all_templates(tmpdir):
    """Check that generate_all_templates appears to, in fact, generate all templates."""
    generate_all_templates(tmpdir)

    # Run twice to ensure we overwrite files without issue
    generate_all_templates(tmpdir)

    # Check that the right number of empty templates was generated
    schema_files = []
    for _, _, fs in os.walk(TEMPLATE_DIR):
        schema_files += [f for f in fs if not f[0] == "."]
    generated_files = [f for _, _, fs in os.walk(tmpdir) for f in fs]
    assert len(schema_files) == len(generated_files)

    # Check that the empty templates have the right names
    generated_filenames = set(f.rstrip(".xlsx") for f in generated_files)
    schema_filenames = set(f.rstrip(".json") for f in schema_files)
    assert generated_filenames == schema_filenames
