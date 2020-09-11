# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.template` module."""

import os
import pytest

from cidc_schemas.constants import TEMPLATE_DIR
from cidc_schemas.template import (
    Template,
    generate_empty_template,
    generate_all_templates,
    ParsingException,
    AtomicChange,
    _FieldDef,
    _get_facet_group,
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


def test_process_field_value():

    schema = {
        "properties": {
            "worksheets": {
                "worksheet_1": {
                    "prism_preamble_object_pointer": "/prism_preamble_object_pointer/0",
                    "preamble_rows": {
                        "preamble_field_1": {
                            "merge_pointer": "/preamble_field",
                            "type": "string",
                        }
                    },
                    "prism_data_object_pointer": "/prism_data_object_pointer/-",
                    "data_columns": {
                        "section_1": {
                            "data_field_1": {
                                "merge_pointer": "/data_field",
                                "type": "number",
                            }
                        }
                    },
                }
            }
        }
    }

    template = Template(schema, type="adhoc_test_template")

    # process_field_value throws a ParsingException on properties missing from the key lookup dict
    with pytest.raises(ParsingException, match="Unexpected property"):
        template.process_field_value("worksheet_1", "unexpected_prop", "123", {}, {})

    with pytest.raises(ParsingException, match="Unexpected worksheet"):
        template.process_field_value("unexpected_worksheet", "whatever", "123", {}, {})

    # not throwing on expected
    template.process_field_value("worksheet_1", "data_field_1", "123", {}, {})


def test_template_arbitrary_data_section():
    schema = {
        "properties": {
            "worksheets": {
                "worksheet_1": {
                    "prism_data_object_pointer": "/prism_data_object_pointer/-",
                    "prism_arbitrary_data_section": "extra_annotations",
                    "prism_arbitrary_data_merge_pointer": "/extra_annotations_sub_object",
                    "data_columns": {
                        "section_1": {
                            "data_field_1": {
                                "merge_pointer": "/data_field",
                                "type": "number",
                            }
                        }
                    },
                }
            }
        }
    }

    template = Template(schema, type="adhoc_arbitrary_data_test_template")

    # not throwing on expected
    changes, _ = template.process_field_value(
        "worksheet_1", "data_field_1", "123", {}, {}
    )

    assert len(changes) == 1
    assert changes[0].pointer == "/data_field"
    assert changes[0].value == 123.0

    # process_field_value DOESN'T throw a ParsingException
    # on arbitrary, not predefined fields
    changes, _ = template.process_field_value(
        "worksheet_1", "unexpected_property", 321, {}, {}
    )

    assert len(changes) == 1
    assert changes[0].pointer == "/extra_annotations_sub_object/unexpected_property"
    assert changes[0].value == 321

    # Checking different keys sanitization
    # TODO - figure out and add more
    changes, _ = template.process_field_value(
        "worksheet_1", "unexpected '\"property", 321, {}, {}
    )

    assert changes[0].pointer == "/extra_annotations_sub_object/unexpected '\"property"


def test_template_schema_checks():
    schema = {
        "properties": {
            "worksheets": {
                "worksheet_1": {
                    "prism_preamble_object_pointer": "/prism_preamble_object_pointer/0",
                    "preamble_rows": {
                        "preamble_field_1": {"gcs_uri_format": "should not be here"}
                    },
                    "prism_data_object_pointer": "/prism_data_object_pointer/-",
                    "data_columns": {
                        "section_1": {
                            "data_field_1": {
                                "merge_pointer": "/data_field",
                                "type": "number",
                                "is_artifact": True,
                            }
                        }
                    },
                }
            }
        }
    }

    with pytest.raises(
        Exception,
        match="Error in template 'adhoc_test_template'/'worksheet_1': Couldn't load mapping for 'preamble_field_1': Either \"type\".*should be present",
    ):
        template = Template(schema, type="adhoc_test_template")

    schema["properties"]["worksheets"]["worksheet_1"]["preamble_rows"][
        "preamble_field_1"
    ]["type"] = "string"

    with pytest.raises(Exception, match=r"missing.*required.*argument.*merge_pointer"):
        template = Template(schema, type="adhoc_test_template")

    schema["properties"]["worksheets"]["worksheet_1"]["preamble_rows"][
        "preamble_field_1"
    ]["merge_pointer"] = "preamble_field"

    with pytest.raises(Exception, match="gcs_uri_format defined for not is_artifact"):
        template = Template(schema, type="adhoc_test_template")

    del schema["properties"]["worksheets"]["worksheet_1"]["preamble_rows"][
        "preamble_field_1"
    ]["gcs_uri_format"]

    with pytest.raises(Exception, match="Empty gcs_uri_format"):
        template = Template(schema, type="adhoc_test_template")

    schema["properties"]["worksheets"]["worksheet_1"]["data_columns"]["section_1"][
        "data_field_1"
    ]["gcs_uri_format"] = 123

    with pytest.raises(Exception, match=r"Bad gcs_uri_format.*should be dict or str"):
        template = Template(schema, type="adhoc_test_template")

    schema["properties"]["worksheets"]["worksheet_1"]["data_columns"]["section_1"][
        "data_field_1"
    ]["gcs_uri_format"] = {"check_errors": "something"}

    with pytest.raises(
        Exception, match="dict type gcs_uri_format should have 'format'"
    ):
        template = Template(schema, type="adhoc_test_template")

    schema["properties"]["worksheets"]["worksheet_1"]["data_columns"]["section_1"][
        "data_field_1"
    ]["gcs_uri_format"] = {"check_errors": "something", "format": "/some/{thing}"}

    template = Template(schema, type="adhoc_test_template")


def test_field_def_process_value():
    prop = "prop0"

    prop_def = {"merge_pointer": "/hello", "coerce": int, "key_name": prop}

    # process_value behaves as expected on a simple example
    changes, files = _FieldDef(**prop_def).process_value("123", {}, {})
    assert changes == [AtomicChange("/hello", 123)]
    assert files == []

    # process_value catches unparseable raw values
    with pytest.raises(ParsingException, match=f"Can't parse {prop!r}"):
        _FieldDef(**prop_def).process_value("123abcd", {}, {})

    # process_value catches a missing gcs_uri_format on an artifact
    prop_def = {
        "merge_pointer": "/hello",
        "coerce": str,
        "is_artifact": 1,
        "key_name": "hello",
    }

    # process_value catches gcs_uri_format strings that can't be processed
    prop_def["gcs_uri_format"] = "{foo}/{bar}"
    with pytest.raises(ParsingException, match="Can't format destination gcs uri"):
        _FieldDef(**prop_def).process_value("123", {}, {})

    prop_def["gcs_uri_format"] = {"format": prop_def["gcs_uri_format"]}
    with pytest.raises(ParsingException, match="Can't format destination gcs uri"):
        _FieldDef(**prop_def).process_value("123", {}, {})


def test_get_facet_group():
    """Check that the _get_facet_group helper function produces facet groups as expected"""
    test_lambda = "lambda val, ctx: '/some/' + str(ctx['foo']) + '/' + val + '_bar.csv'"
    assert _get_facet_group(test_lambda) == "/some/_bar.csv"

    test_fmt_string = "/some/{a_b}/{c-d}/foo/{buzz123}/{OK}_bar.csv"
    assert _get_facet_group(test_fmt_string) == "/some/foo/_bar.csv"


def test_from_type():
    pbmc = Template.from_type("pbmc")

    assert "Shipment" in pbmc.worksheets
    assert "Samples" in pbmc.worksheets
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
