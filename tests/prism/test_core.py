"""Tests for generic prismification functionality.

TODO: some of these tests currently use the CIDC data model, but they 
should probably use an unrelated test data model instead.
"""
from unittest.mock import MagicMock
from collections import namedtuple

import pytest

from cidc_schemas.template import Template
from cidc_schemas.template_reader import XlTemplateReader
from cidc_schemas import prism
from cidc_schemas.prism import core

#### HELPER FUNCTION TESTS ####


def test_set_val():
    """Test the _set_val helper function directly, since it's prismify workhorse"""
    # _set_val should handle the basic example in the _set_val docstring
    context = {"Pid": 1}
    root = {"prop0": [context]}
    core._set_val("0/prop1/prop2", {"more": "props"}, context, root, "/prop0/0")
    assert root == {"prop0": [{"Pid": 1, "prop1": {"prop2": {"more": "props"}}}]}

    # _set_val should set nested lists
    context = []
    root = {"prop0": context}
    core._set_val("0/-/-", [1, 2, 3], context, root, "/prop0")
    assert root == {"prop0": [[[1, 2, 3]]]}

    # _set_val overwrites when adding a value to particular location in a list
    # TODO: is this the behavior we want?
    context = [[], ["will be overwritten"]]
    root = {"prop0": context}
    core._set_val("0/1", [1, 2, 3], context, root, "/prop0")
    assert root == {"prop0": [[], [1, 2, 3]]}

    # _set_val shouldn't make any modifications to `root` if `val == None`
    context = {"Pid": 1}
    root = {"prop0": [context]}
    core._set_val("0/prop1/prop2", None, context, root, "/prop0/0")
    assert root == {"prop0": [context]}

    # _set_val should throw an exception given a value pointer with too many jumps
    with pytest.raises(AssertionError, match="too many jumps up"):
        core._set_val("3/prop1/prop2", {}, {}, {}, "/prop0/0")

    # _set_val should throw an exception given an invalid context pointer
    one_jumpup_pointer = "1/prop1"
    invalid_context_pointer = "/foo/bar"
    with pytest.raises(Exception, match="member 'foo' not found"):
        core._set_val(one_jumpup_pointer, {}, {}, {}, invalid_context_pointer)


def test_process_property():
    prop = "prop0"

    # _process_property throws a ParsingException on properties missing from the key lookup dict
    with pytest.raises(prism.ParsingException, match="Unexpected property"):
        core._process_property(prop, "123", {}, {}, {})

    prop_def = {"merge_pointer": "/hello", "coerce": int, "key_name": "hello"}

    # _process_property behaves as expected on a simple example
    root = {}
    files = core._process_property(prop, "123", {prop: prop_def}, root, {})
    assert root == {"hello": 123}
    assert files == []

    # _process_property catches unparseable raw values
    with pytest.raises(prism.ParsingException, match=f"Can't parse {prop!r}"):
        core._process_property(prop, "123abcd", {prop: prop_def}, {}, {})

    # _process_property catches a missing gcs_uri_format on an artifact
    prop_def = {
        "merge_pointer": "/hello",
        "coerce": str,
        "is_artifact": 1,
        "key_name": "hello",
    }
    with pytest.raises(prism.ParsingException, match="Empty gcs_uri_format"):
        core._process_property(prop, "123", {prop: prop_def}, {}, {})

    # _process property catches gcs_uri_format strings that can't be processed
    prop_def["gcs_uri_format"] = "{foo}/{bar}"
    with pytest.raises(prism.ParsingException, match="Can't format gcs uri"):
        core._process_property(prop, "123", {prop: prop_def}, {}, {})

    prop_def["gcs_uri_format"] = {"format": prop_def["gcs_uri_format"]}
    with pytest.raises(prism.ParsingException, match="Can't format gcs uri"):
        core._process_property(prop, "123", {prop: prop_def}, {}, {})


#### END HELPER FUNCTION TESTS ####


#### PRISMIFY TESTS ####


def test_unsupported_prismify():
    """Check that prism raises a non-implemented error for unsupported template types."""
    mock_template = MagicMock()
    mock_template.type = "some-unsupported-type"

    with pytest.raises(
        NotImplementedError, match="'some-unsupported-type' is not supported"
    ):
        core.prismify(None, mock_template)


def mock_XlTemplateReader_from_excel(sheets: dict, monkeypatch):

    load_workbook = MagicMock(name="load_workbook")
    monkeypatch.setattr("openpyxl.load_workbook", load_workbook)
    workbook = load_workbook.return_value = MagicMock(name="workbook")

    wb = {k: MagicMock(name=k) for k in sheets}

    workbook.__getitem__.side_effect = wb.__getitem__
    workbook.sheetnames = sheets.keys()
    cell = namedtuple("cell", ["value"])

    for k, rows in sheets.items():
        wb[k].iter_rows.return_value = [map(cell, r) for r in rows]

    return


def test_prismify_unexpected_worksheet(monkeypatch):
    """Check that prismify catches the presence of an unexpected worksheet in an Excel template."""
    mock_XlTemplateReader_from_excel({"whoops": []}, monkeypatch)
    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    template = Template(
        {"title": "unexpected worksheet", "properties": {"worksheets": {}}},
        "test_unexpected_worksheet",
    )
    monkeypatch.setattr(
        "cidc_schemas.prism.core.SUPPORTED_TEMPLATES", ["test_unexpected_worksheet"]
    )

    _, _, errs = core.prismify(xlsx, template)
    assert errs == ["Unexpected worksheet 'whoops'."]


def test_prismify_preamble_parsing_error(monkeypatch):
    """Check that prismify catches parsing errors in the pre"""
    prop = "prop0"
    raw_val = "some string"
    mock_XlTemplateReader_from_excel({"ws1": [["#p", prop, raw_val]]}, monkeypatch)
    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    template = Template(
        {
            "title": "parse error",
            "properties": {
                "worksheets": {
                    "ws1": {
                        "prism_preamble_object_schema": "clinical_trial.json",
                        "prism_preamble_object_pointer": "#",
                        "prism_data_object_pointer": "/files/-",
                        "preamble_rows": {
                            prop: {"merge_pointer": "/", "type": "number"}
                        },
                    }
                }
            },
        },
        "test_preamble_parsing_error",
    )
    monkeypatch.setattr(
        "cidc_schemas.prism.core.SUPPORTED_TEMPLATES", ["test_preamble_parsing_error"]
    )

    _, _, errs = core.prismify(xlsx, template)
    assert isinstance(errs[0], prism.ParsingException)


def test_prism_local_files_format_extension(monkeypatch):
    """ Tests prism alert on different extensions of a local file vs gcs_uri """

    mock_XlTemplateReader_from_excel(
        {
            "files": [
                ["#h", "record", "local_file_col_name"],
                ["#d", "1", "somewhere/on/my/computer.csv"],
                ["#d", "2", "somewhere/on/my/computer.xlsx"],
            ]
        },
        monkeypatch,
    )

    template = Template(
        {
            "$id": "test_files",
            "title": "files",
            "properties": {
                "worksheets": {
                    "files": {
                        "prism_preamble_object_schema": "clinical_trial.json",
                        "prism_preamble_object_pointer": "#",
                        "prism_data_object_pointer": "/files/-",
                        "preamble_rows": {},
                        "data_columns": {
                            "Files": {
                                "record": {"merge_pointer": "/id", "type": "number"},
                                "local_file_col_name": {
                                    "merge_pointer": "artifact",
                                    "gcs_uri_format": "{record}/artifact.csv",
                                    "is_artifact": 1,
                                    "type_ref": "assays/components/local_file.json#properties/file_path",
                                },
                            }
                        },
                    }
                }
            },
        },
        "test_prism_local_files_format_extension",
    )

    monkeypatch.setattr(
        "cidc_schemas.prism.core.SUPPORTED_TEMPLATES",
        ["test_prism_local_files_format_extension"],
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    patch, file_maps, errs = core.prismify(xlsx, template)

    assert len(errs) == 1
    assert "local_file_col_name" in str(errs[0])
    assert "expected .csv" in str(errs[0]).lower()

    assert len(file_maps) == 1


def test_prism_local_files_format_multiple_extensions(monkeypatch):
    """ Tests prism ability to gcs_uri """

    mock_XlTemplateReader_from_excel(
        {
            "files": [
                ["#h", "record", "local_file_col_name"],
                ["#d", "1", "somewhere/on/my/computer.tif"],
                ["#d", "2", "somewhere/on/my/computer.tiff"],
                ["#d", "3", "somewhere/on/my/computer.NONtiff"],
                ["#d", "4", "somewhere/on/my/computer.svs"],
                ["#d", "5", "somewhere/on/my/computer.qptiff"],
            ]
        },
        monkeypatch,
    )

    template = Template(
        {
            "$id": "test_files",
            "title": "files",
            "properties": {
                "worksheets": {
                    "files": {
                        "prism_preamble_object_schema": "clinical_trial.json",
                        "prism_preamble_object_pointer": "#",
                        "prism_data_object_pointer": "/files/-",
                        "preamble_rows": {},
                        "data_columns": {
                            "Files": {
                                "record": {"merge_pointer": "/id", "type": "number"},
                                "local_file_col_name": {
                                    "merge_pointer": "artifact",
                                    "gcs_uri_format": {
                                        "format": "lambda val, ctx: 'subfolder/' + ctx['record'] + '/artifact.' + val.rsplit('.', 1)[-1]",
                                        "check_errors": "lambda val: f'Bad file type {val!r}. It should be in one of .tiff .tif .qptiff .svs formats' if val.rsplit('.', 1)[-1] not in ['svs', 'tiff', 'tif', 'qptiff'] else None",
                                        "template_comment": "In one of .tiff .tif .qptiff .svs formats.",
                                    },
                                    "is_artifact": 1,
                                    "type_ref": "assays/components/local_file.json#properties/file_path",
                                },
                            }
                        },
                    }
                }
            },
        },
        "test_prism_local_files_format_extension",
    )

    monkeypatch.setattr(
        "cidc_schemas.prism.core.SUPPORTED_TEMPLATES",
        ["test_prism_local_files_format_extension"],
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    patch, file_maps, errs = core.prismify(xlsx, template)

    assert len(errs) == 1
    assert "Bad file type" in str(errs[0])
    assert ".NONtiff" in str(errs[0])
    assert "should be in one of" in str(errs[0])

    assert len(file_maps) == 4
    expected_extensions = ["tif", "tiff", "svs", "qptiff"]
    # check that we have only "proper" (checked by `check_errors`) extensions
    local_extensions = [core._get_file_ext(fm.local_path) for fm in file_maps]
    gcs_extensions = [core._get_file_ext(fm.gs_key) for fm in file_maps]
    assert expected_extensions == gcs_extensions == local_extensions


def test_prism_joining_tabs(monkeypatch):
    """ Tests whether prism can join data from two excel tabs for a shared metadata subtree """

    mock_XlTemplateReader_from_excel(
        {
            "participants": [
                ["#h", "PA id", "PA prop"],
                ["#d", "CPP0", "0"],
                ["#d", "CPP1", "1"],
            ],
            "samples": [
                ["#h", "SA_id", "SA_prop"],
                ["#d", "CPP1S0.00", "100"],
                ["#d", "CPP1S1.00", "101"],
                ["#d", "CPP0S0.00", "000"],
                ["#d", "CPP0S1.00", "001"],
            ],
        },
        monkeypatch,
    )

    template = Template(
        {
            "$id": "test_ship",
            "title": "participants and shipment",
            "properties": {
                "worksheets": {
                    "participants": {
                        "prism_preamble_object_schema": "clinical_trial.json",
                        "prism_preamble_object_pointer": "#",
                        "prism_data_object_pointer": "/participants/0/samples/0",
                        "preamble_rows": {},
                        "data_columns": {
                            "Samples": {
                                "PA id": {
                                    "merge_pointer": "2/cimac_participant_id",
                                    "type_ref": "participant.json#properties/cimac_participant_id",
                                },
                                "PA prop": {
                                    "merge_pointer": "0/participant_id",
                                    "type_ref": "participant.json#properties/participant_id",
                                },
                            }
                        },
                    },
                    "samples": {
                        "prism_preamble_object_schema": "clinical_trial.json",
                        "prism_preamble_object_pointer": "#",
                        "prism_data_object_pointer": "/participants/0/samples/0",
                        "preamble_rows": {},
                        "data_columns": {
                            "Samples": {
                                "SA_id": {
                                    "merge_pointer": "/cimac_id",
                                    "type_ref": "sample.json#properties/cimac_id",
                                    "process_as": [
                                        {
                                            "merge_pointer": "2/cimac_participant_id",
                                            "parse_through": "lambda x: x[:4]",
                                            "type_ref": "participant.json#properties/cimac_participant_id",
                                        }
                                    ],
                                },
                                "SA_prop": {
                                    "merge_pointer": "0/parent_sample_id",
                                    "type_ref": "sample.json#properties/parent_sample_id",
                                },
                            }
                        },
                    },
                }
            },
        },
        "test_prism_joining_tabs",
    )

    monkeypatch.setattr(
        "cidc_schemas.prism.core.SUPPORTED_TEMPLATES", ["test_prism_joining_tabs"]
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    patch, file_maps, errs = core.prismify(xlsx, template)
    assert len(errs) == 0

    assert 2 == len(patch["participants"])

    assert "CPP0" == patch["participants"][0]["cimac_participant_id"]
    assert 2 == len(patch["participants"][0]["samples"])

    assert "CPP0S0.00" == patch["participants"][0]["samples"][0]["cimac_id"]
    assert "000" == patch["participants"][0]["samples"][0]["parent_sample_id"]

    assert "CPP0S1.00" == patch["participants"][0]["samples"][1]["cimac_id"]
    assert "001" == patch["participants"][0]["samples"][1]["parent_sample_id"]

    assert "CPP1S1.00" == patch["participants"][1]["samples"][1]["cimac_id"]
    assert "101" == patch["participants"][1]["samples"][1]["parent_sample_id"]

    assert "CPP1" == patch["participants"][1]["cimac_participant_id"]
    assert 2 == len(patch["participants"][1]["samples"])

    assert 0 == len(file_maps)


def test_prism_process_as_error(monkeypatch):
    """Tests that prismify doesn't crash when a `parse_through` function errors"""
    mock_XlTemplateReader_from_excel(
        {
            "participants": [["#h", "PA_id"], ["#d", "CPP0"]],
            "samples": [["#h", "SA_id", "SA_prop"], ["#d", None, 100]],
        },
        monkeypatch,
    )

    template = Template(
        {
            "$id": "test_ship",
            "title": "participants and shipment",
            "properties": {
                "worksheets": {
                    "participants": {
                        "prism_preamble_object_schema": "clinical_trial.json",
                        "prism_preamble_object_pointer": "#",
                        "prism_data_object_pointer": "/participants/0/samples/0",
                        "preamble_rows": {},
                        "data_columns": {
                            "Samples": {
                                "PA_id": {
                                    "merge_pointer": "2/cimac_participant_id",
                                    "type_ref": "participant.json#properties/cimac_participant_id",
                                }
                            }
                        },
                    },
                    "samples": {
                        "prism_preamble_object_schema": "clinical_trial.json",
                        "prism_preamble_object_pointer": "#",
                        "prism_data_object_pointer": "/participants/0/samples/0",
                        "preamble_rows": {},
                        "data_columns": {
                            "Samples": {
                                "SA_id": {
                                    "merge_pointer": "/cimac_id",
                                    "type_ref": "sample.json#properties/cimac_id",
                                    "process_as": [
                                        {
                                            "merge_pointer": "2/cimac_participant_id",
                                            "parse_through": "lambda x: x[:4]",
                                            "type_ref": "participant.json#properties/cimac_participant_id",
                                        }
                                    ],
                                },
                                "SA_prop": {
                                    "merge_pointer": "0/parent_sample_id",
                                    "type_ref": "sample.json#properties/parent_sample_id",
                                },
                            }
                        },
                    },
                }
            },
        },
        "test_prism_process_as",
    )
    monkeypatch.setattr(
        "cidc_schemas.prism.core.SUPPORTED_TEMPLATES", ["test_prism_process_as"]
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    patch, file_maps, errs = core.prismify(xlsx, template)
    assert "Cannot extract cimac_participant_id from SA_id value: None" == str(errs[0])


def test_prism_many_artifacts_from_process_as_on_one_record(monkeypatch):
    """ Tests whether prism can join data from two excel tabs for a shared metadata subtree """

    mock_XlTemplateReader_from_excel(
        {
            "analysis": [
                ["#h", "run_id", "sid1", "sid2"],
                ["#d", "000", "sid1_0", "sid2_0"],
                ["#d", "111", "sid1_1", "sid2_1"],
            ]
        },
        monkeypatch,
    )

    template = Template(
        {
            "$id": "test_analysis",
            "title": "...",
            "prism_template_root_object_schema": "assays/components/ngs/wes/wes_analysis.json",
            "prism_template_root_object_pointer": "/analysis/wes_analysis",
            "properties": {
                "worksheets": {
                    "analysis": {
                        "prism_data_object_pointer": "/pair_runs/-",
                        "preamble_rows": {},
                        "data_columns": {
                            "section name": {
                                "run_id": {
                                    "merge_pointer": "/run_id",
                                    "type": "string",
                                    "process_as": [
                                        {
                                            "parse_through": "lambda x: f'analysis/germline/{x}/{x}-run-output-1.txt'",
                                            "merge_pointer": "/run-output-1",
                                            "gcs_uri_format": "{run_id}/run-output-1.txt",
                                            "type_ref": "assays/components/local_file.json#properties/file_path",
                                            "is_artifact": 1,
                                        },
                                        {
                                            "parse_through": "lambda x: f'analysis/purity/{x}/{x}run-output-2.txt'",
                                            "merge_pointer": "/run-output-2",
                                            "gcs_uri_format": "{run_id}/run-output-2.txt",
                                            "type_ref": "assays/components/local_file.json#properties/file_path",
                                            "is_artifact": 1,
                                        },
                                        {
                                            "parse_through": "lambda x: f'analysis/clonality/{x}/{x}-run-output-3.tsv'",
                                            "merge_pointer": "/run-output-3",
                                            "gcs_uri_format": "{run_id}/run-output-3.tsv",
                                            "type_ref": "assays/components/local_file.json#properties/file_path",
                                            "is_artifact": 1,
                                        },
                                    ],
                                },
                                "sid1": {
                                    "merge_pointer": "/sample1/id",
                                    "type": "string",
                                    "process_as": [
                                        {
                                            "parse_through": "lambda x: f'analysis/align/{x}/{x}.output1.bam'",
                                            "merge_pointer": "/sample1/output1",
                                            "gcs_uri_format": "{run_id}/{sid1}/output1.bam",
                                            "type_ref": "assays/components/local_file.json#properties/file_path",
                                            "is_artifact": 1,
                                        },
                                        {
                                            "parse_through": "lambda x: f'analysis/metrics/{x}/{x}.output2.txt'",
                                            "merge_pointer": "/sample1/output2",
                                            "gcs_uri_format": "{run_id}/{sid1}/output2.txt",
                                            "type_ref": "assays/components/local_file.json#properties/file_path",
                                            "is_artifact": 1,
                                        },
                                        {
                                            "parse_through": "lambda x: f'analysis/optitype/{x}/{x}output3.tsv'",
                                            "merge_pointer": "/sample1/output3",
                                            "gcs_uri_format": "{run_id}/{sid1}/output3.tsv",
                                            "type_ref": "assays/components/local_file.json#properties/file_path",
                                            "is_artifact": 1,
                                        },
                                    ],
                                },
                                "sid2": {
                                    "merge_pointer": "/sample2/id",
                                    "type": "string",
                                    "process_as": [
                                        {
                                            "parse_through": "lambda x: f'analysis/align/{x}/{x}.output1.bam'",
                                            "merge_pointer": "/sample2/output1",
                                            "gcs_uri_format": "{run_id}/{sid2}/output1.bam",
                                            "type_ref": "assays/components/local_file.json#properties/file_path",
                                            "is_artifact": 1,
                                        },
                                        {
                                            "parse_through": "lambda x: f'analysis/metrics/{x}/{x}.output2.txt'",
                                            "merge_pointer": "/sample2/output2",
                                            "gcs_uri_format": "{run_id}/{sid2}/output2.txt",
                                            "type_ref": "assays/components/local_file.json#properties/file_path",
                                            "is_artifact": 1,
                                        },
                                        {
                                            "parse_through": "lambda x: f'analysis/optitype/{x}/{x}.output3.tsv'",
                                            "merge_pointer": "/sample2/output3",
                                            "gcs_uri_format": "{run_id}/{sid2}/output3.tsv",
                                            "type_ref": "assays/components/local_file.json#properties/file_path",
                                            "is_artifact": 1,
                                        },
                                    ],
                                },
                            }
                        },
                    }
                }
            },
        },
        "test_prism_many_artifacts_from_process_as_on_one_record",
    )

    monkeypatch.setattr(
        "cidc_schemas.prism.core.SUPPORTED_TEMPLATES",
        ["test_prism_many_artifacts_from_process_as_on_one_record"],
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    patch, file_maps, errs = core.prismify(xlsx, template)
    assert len(errs) == 0

    local_paths = [e.local_path for e in file_maps]
    uuids = [e.upload_placeholder for e in file_maps]

    assert 3 * 3 * 2 == len(
        file_maps
    )  # (3 files * 3 fields from each record) * 2 records
    assert 3 * 3 * 2 == len(
        set(uuids)
    )  # (3 files * 3 fields from each record) * 2 records

    assert local_paths != uuids

    assert 2 == len(patch["analysis"]["wes_analysis"]["pair_runs"])
    run_uuids_in_json = [
        art["upload_placeholder"]
        for wes in patch["analysis"]["wes_analysis"]["pair_runs"]
        for art in wes.values()
        if "upload_placeholder" in art
    ]
    sample_uuids_in_json = [
        v["upload_placeholder"]
        for wes in patch["analysis"]["wes_analysis"]["pair_runs"]
        for sample in wes.values()
        if "id" in sample
        for v in sample.values()
        if "upload_placeholder" in v
    ]

    assert len(uuids) == len(run_uuids_in_json + sample_uuids_in_json)
    assert set(uuids) == set(
        run_uuids_in_json + sample_uuids_in_json
    )  # set instead of sorting


#### END PRISMIFY TESTS ####
