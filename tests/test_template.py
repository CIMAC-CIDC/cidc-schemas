# -*- coding: utf-8 -*-

"""Tests for `cidc_schemas.template` module."""

from deepdiff import DeepDiff
import json
import os
import pytest

from cidc_schemas.constants import SCHEMA_DIR, TEMPLATE_DIR
from cidc_schemas.prism import InvalidMergeTargetException
from cidc_schemas.json_validation import _load_dont_validate_schema

from cidc_schemas.template import (
    Template,
    generate_empty_template,
    generate_all_templates,
    ParsingException,
    AtomicChange,
    _FieldDef,
    _get_facet_group,
    _convert_api_to_template,
    _first_in_context,
    generate_analysis_template_schemas,
)

from .constants import TEST_SCHEMA_DIR

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
    with pytest.raises(ParsingException, match="Can't format destination gcs uri"):
        _FieldDef(**prop_def).process_value("123", {}, {})

    # process_value catches gcs_uri_format strings that can't be processed
    prop_def["gcs_uri_format"] = "{foo}/{bar}"
    with pytest.raises(ParsingException, match="Can't format destination gcs uri"):
        _FieldDef(**prop_def).process_value("123", {}, {})

    prop_def["gcs_uri_format"] = {"format": prop_def["gcs_uri_format"]}
    with pytest.raises(ParsingException, match="Can't format destination gcs uri"):
        _FieldDef(**prop_def).process_value("123", {}, {})

    # process_value does remove brackets from gcs uri
    prop_def["gcs_uri_format"] = "[foo].bar"
    changes, files = _FieldDef(**prop_def).process_value("baz.bar", {}, {})
    assert files[0].gs_key == "foo.bar"


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


@pytest.mark.xfail(reason="flaky xlsx binary comparison")
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


def test_first_in_context():
    context = {
        "key1": {"properties": {}},
        "key1_key2": {"properties": {}},  # more specific
        "key2_key3": {"properties": {}},  # two with underscore
        "key4key5": {"properties": {}},  # two without underscore
        "key6_index": {"properties": {}},  # index
        "key7_summary": {"properties": {}},  # summary
    }

    # Identical
    assert _first_in_context(["key1"], context)[0] == "key1"

    # More specific
    assert _first_in_context(["key1", "key2"], context)[0] == "key1_key2"

    # Key has dot, context has underscore
    assert _first_in_context(["key2.key3"], context)[0] == "key2_key3"

    # Key has dot, context only has first half
    assert _first_in_context(["Key1.key3"], context)[0] == "key1"

    # Pull summary from end
    assert (
        _first_in_context(["key7", "this_is_missed", ".summary.txt"], context)[0]
        == "key7_summary"
    )

    # Two joined with underscore
    assert _first_in_context(["key2", "key3"], context)[0] == "key2_key3"

    # Skipping logs
    assert _first_in_context(["logs", "Key1"], context)[0] == "key1"

    # Key missing underscore
    assert _first_in_context(["key2key3"], context)[0] == "key2_key3"

    # Key has extra underscore
    assert _first_in_context(["key4_key5"], context)[0] == "key4key5"

    # Two joined, but then has extra underscore
    assert _first_in_context(["key4", "key5"], context)[0] == "key4key5"

    # Dot -> underscore, but then has extra underscore
    assert _first_in_context(["key4.key5"], context)[0] == "key4key5"

    # Drop bam from bam_index
    assert _first_in_context(["key6_bam_index"], context)[0] == "key6_index"

    # Capitals
    assert _first_in_context(["Key1"], context)[0] == "key1"

    # items with one-element path
    assert _first_in_context(["foo"], {"foo": {"items": {"properties": "bar"}}}) == (
        "foo",
        [],
        "bar",
    )

    # items with two-element path
    assert _first_in_context(
        ["foo", "bar"], {"foo": {"items": {"properties": "bar"}}}
    ) == ("foo", ["bar"], "bar")


def test_convert_api_to_template_wes():
    wes_api = {
        "run id": [
            {
                "filter_group": "clonality/clonality_pyclone",
                "file_path_template": "analysis/clonality/{run id}/{run id}_pyclone.tsv",
                "short_description": "clonality_pyclone file",
                "long_description": "clonality_pyclone file clonality_pyclone file",
                "file_purpose": "Miscellaneous",
            }
        ],
        "tumor cimac id": [
            {
                "filter_group": "alignment/align_sorted_dedup",
                "file_path_template": "analysis/align/{tumor cimac id}/{tumor cimac id}.sorted.dedup.bam",
                "short_description": "align_sorted_dedup file",
                "long_description": "align_sorted_dedup file align_sorted_dedup file",
                "file_purpose": "Miscellaneous",
            }
        ],
    }

    wes_json = {
        "title": "WES analysis template",
        "description": "Metadata information for WES Analysis output.",
        "prism_template_root_object_schema": "assays/components/ngs/wes/wes_analysis.json",
        "prism_template_root_object_pointer": "/analysis/wes_analysis",
        "properties": {
            "worksheets": {
                "WES Analysis": {
                    "preamble_rows": {
                        "protocol identifier": {
                            "merge_pointer": "2/protocol_identifier",
                            "type_ref": "clinical_trial.json#properties/protocol_identifier",
                        }
                    },
                    "prism_data_object_pointer": "/pair_runs/-",
                    "data_columns": {
                        "WES Runs": {
                            "run id": {
                                "merge_pointer": "/run_id",
                                "type_ref": "assays/components/ngs/wes/wes_pair_analysis.json#properties/run_id",
                                "process_as": [
                                    {
                                        "parse_through": "lambda run: f'analysis/clonality/{run}/{run}_pyclone.tsv'",
                                        "merge_pointer": "/clonality/clonality_pyclone",
                                        "gcs_uri_format": "{protocol identifier}/wes/{run id}/analysis/clonality_pyclone.tsv",
                                        "type_ref": "assays/components/local_file.json#properties/file_path",
                                        "is_artifact": 1,
                                    }
                                ],
                            },
                            "tumor cimac id": {
                                "merge_pointer": "/tumor/cimac_id",
                                "type_ref": "sample.json#properties/cimac_id",
                                "process_as": [
                                    {
                                        "parse_through": "lambda id: f'analysis/align/{id}/{id}.sorted.dedup.bam'",
                                        "merge_pointer": "/tumor/alignment/align_sorted_dedup",
                                        "gcs_uri_format": "{protocol identifier}/wes/{run id}/analysis/tumor/{tumor cimac id}/sorted.dedup.bam",
                                        "type_ref": "assays/components/local_file.json#properties/file_path",
                                        "is_artifact": 1,
                                    }
                                ],
                            },
                        }
                    },
                }
            }
        },
    }

    assay_schema = _load_dont_validate_schema(
        "assays/components/ngs/wes/wes_analysis.json"
    )

    wes_output = _convert_api_to_template("wes", wes_api, assay_schema)
    assert DeepDiff(wes_json, wes_output) == {}


def test_convert_api_to_template_rna():
    rna_api = {
        "cimac id": [
            {  # use first entry as example
                "filter_group": "alignment",
                "file_path_template": "analysis/star/{id}/{id}.sorted.bam",
                "short_description": "star alignment output",
                "long_description": "file sorted_bam file sorted_bam file sorted_bam file",
                "file_purpose": "Analysis view",
            }
        ]
    }

    rna_json = {
        "title": "RNAseq level 1 analysis template",
        "description": "Metadata information for RNAseq level 1 Analysis output.",
        "prism_template_root_object_schema": "assays/components/ngs/rna/rna_analysis.json",
        "prism_template_root_object_pointer": "/analysis/rna_analysis",
        "properties": {
            "worksheets": {
                "RNAseq Analysis": {
                    "preamble_rows": {
                        "protocol identifier": {
                            "merge_pointer": "2/protocol_identifier",
                            "type_ref": "clinical_trial.json#properties/protocol_identifier",
                        }
                    },
                    "prism_data_object_pointer": "/level_1/-",
                    "data_columns": {
                        "RNAseq Runs": {
                            "cimac id": {
                                "merge_pointer": "/cimac_id",
                                "type_ref": "sample.json#properties/cimac_id",
                                "process_as": [
                                    {
                                        "parse_through": "lambda id: f'analysis/star/{id}/{id}.sorted.bam'",
                                        "merge_pointer": "0/star/sorted_bam",
                                        "gcs_uri_format": "{protocol identifier}/rna/{cimac id}/analysis/star/sorted.bam",
                                        "type_ref": "assays/components/local_file.json#properties/file_path",
                                        "is_artifact": 1,
                                    }
                                ],
                            }
                        }
                    },
                }
            }
        },
    }

    assay_schema = _load_dont_validate_schema(
        "assays/components/ngs/rna/rna_analysis.json"
    )
    rna_output = _convert_api_to_template("rna", rna_api, assay_schema)
    assert DeepDiff(rna_json, rna_output) == {}

    rna_api_bad_key = {"foo": [{}]}
    with pytest.raises(InvalidMergeTargetException, match="corresponding entry"):
        _convert_api_to_template("rna", rna_api_bad_key, assay_schema)

    rna_api_no_target = {
        "cimac id": [
            {
                "filter_group": "alignment",
                "file_path_template": "foo",  # used to generate merge_pointer
                "short_description": "star alignment output",
                "long_description": "file sorted_bam file sorted_bam file sorted_bam file",
                "file_purpose": "Analysis view",
            }
        ]
    }
    with pytest.raises(InvalidMergeTargetException, match="cannot be mapped"):
        _convert_api_to_template("rna", rna_api_no_target, assay_schema)

    rna_api_merge_collision = {
        "cimac id": [
            {
                "filter_group": "alignment",
                "file_path_template": "analysis/star/{id}/{id}.sorted.bam",
                "short_description": "star alignment output",
                "long_description": "file sorted_bam file sorted_bam file sorted_bam file",
                "file_purpose": "Analysis view",
            },
            {  # direct repeat will collide
                "filter_group": "alignment",
                "file_path_template": "analysis/star/{id}/{id}.sorted.bam",
                "short_description": "star alignment output",
                "long_description": "file sorted_bam file sorted_bam file sorted_bam file",
                "file_purpose": "Analysis view",
            },
        ]
    }
    with pytest.raises(
        InvalidMergeTargetException, match="collision for inferred merge target"
    ):
        _convert_api_to_template("rna", rna_api_merge_collision, assay_schema)


def test_generate_analysis_template_schemas_rna(tmpdir):
    generate_analysis_template_schemas(
        tmpdir.strpath, lambda file: f"{file}_template.json"
    )

    test_dir = os.path.join(TEST_SCHEMA_DIR, "target-templates")
    good_rna = json.load(open(os.path.join(test_dir, "rna_template.json")))

    new_rna = json.load(open(tmpdir.join("rna_template.json")))
    assert DeepDiff(good_rna, new_rna) == {}


def test_generate_analysis_template_schemas_wes(tmpdir):
    generate_analysis_template_schemas(
        tmpdir.strpath, lambda file: f"{file}_template.json"
    )
    test_dir = os.path.join(TEST_SCHEMA_DIR, "target-templates")
    good_wes = json.load(open(os.path.join(test_dir, "wes_template.json")))
    new_wes = json.load(open(tmpdir.join("wes_template.json")))
    assert DeepDiff(good_wes, new_wes) == {}
