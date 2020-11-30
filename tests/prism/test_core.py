"""Tests for generic prismification functionality.

TODO: some of these tests currently use the CIDC data model, but they 
should probably use an unrelated test data model instead.
"""
import os
import base64
import hmac
from unittest.mock import MagicMock
from collections import namedtuple

import pytest

from cidc_schemas.template import Template
from cidc_schemas.template_reader import XlTemplateReader
from cidc_schemas import prism
from cidc_schemas import util
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


TEST_SCHEMA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "schema")


def build_mock_Template(spec: dict, name: str, monkeypatch) -> Template:
    monkeypatch.setattr("cidc_schemas.prism.core.SUPPORTED_TEMPLATES", [name])

    return Template(spec, name, TEST_SCHEMA_DIR)


def test_prismify_unexpected_worksheet(monkeypatch):
    """Check that prismify catches the presence of an unexpected worksheet in an Excel template."""
    mock_XlTemplateReader_from_excel({"whoops": []}, monkeypatch)
    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    template = build_mock_Template(
        {
            "title": "unexpected worksheet",
            "prism_template_root_object_schema": "test_schema.json",
            "properties": {"worksheets": {}},
        },
        "test_unexpected_worksheet",
        monkeypatch,
    )

    _, _, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)
    assert errs == ["Unexpected worksheet 'whoops'."]


def test_prismify_preamble_parsing_error(monkeypatch):
    """Check that prismify catches parsing errors in the pre"""
    prop = "prop0"
    mock_XlTemplateReader_from_excel(
        {"ws1": [["#preamble", prop, "some string"]]}, monkeypatch
    )
    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    template = build_mock_Template(
        {
            "title": "parse error",
            "prism_template_root_object_schema": "test_schema.json",
            "properties": {
                "worksheets": {
                    "ws1": {
                        "prism_preamble_object_schema": "test_schema.json",
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
        monkeypatch,
    )

    _, _, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)
    assert isinstance(errs[0], prism.ParsingException)


def test_encrypt():

    # setup
    core._encrypt_hmac = None

    with pytest.raises(Exception, match="initialized"):
        core._encrypt("x")

    assert not core._encrypt_hmac

    core.set_prism_encrypt_key("key")

    with pytest.raises(Exception, match="twice"):
        core.set_prism_encrypt_key("key")

    assert core._encrypt_hmac

    d = hmac.new(b"key", msg=b"", digestmod="SHA512").digest()
    assert core._encrypt("") == base64.b64encode(d)[:32].decode()
    assert core._encrypt("") == "hPpaoCebvEcyZ9BaU+oDMQqYfOzEwVNf"


def test_prismify_encrypt(monkeypatch):
    """Check that prismify can encrypt private values"""

    # setup
    core._encrypt_hmac = None

    prop = "prop0"
    mock_XlTemplateReader_from_excel(
        {"ws1": [["#preamble", prop, "some str"]]}, monkeypatch
    )
    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    template = build_mock_Template(
        {
            "title": "parse error",
            "prism_template_root_object_schema": "test_schema.json",
            "properties": {
                "worksheets": {
                    "ws1": {
                        "prism_preamble_object_schema": "test_schema.json",
                        "prism_preamble_object_pointer": "#",
                        "prism_data_object_pointer": "/files/-",
                        "preamble_rows": {
                            prop: {
                                "merge_pointer": "/file_path",
                                "type": "string",
                                "encrypt": True,
                            }
                        },
                    }
                }
            },
        },
        "test_preamble_parsing_error",
        monkeypatch,
    )

    # pretend to forgot 'set_prism_encrypt_key' so we get server error
    with pytest.raises(Exception, match="Encrypt is not initialized"):
        core.prismify(xlsx, template, TEST_SCHEMA_DIR)

    core.set_prism_encrypt_key("key")

    patch, _, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)
    assert not errs

    d = hmac.new(b"key", msg=b"some str", digestmod="SHA512").digest()
    encrypted = base64.b64encode(d)[:32].decode()
    assert patch == {"file_path": encrypted}


def test_prism_local_files_format_extension(monkeypatch):
    """ Tests prism alert on different extensions of a local file vs gcs_uri """

    mock_XlTemplateReader_from_excel(
        {
            "files": [
                ["#header", "record", "local_file_col_name"],
                ["#data", "1", "somewhere/on/my/computer.csv"],
                ["#data", "2", "somewhere/on/my/computer.xlsx"],
            ]
        },
        monkeypatch,
    )

    template = build_mock_Template(
        {
            "$id": "test_files",
            "title": "files",
            "prism_template_root_object_schema": "test_schema.json",
            "properties": {
                "worksheets": {
                    "files": {
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
                                    "type_ref": "test_schema.json#/definitions/file_path",
                                },
                            }
                        },
                    }
                }
            },
        },
        "test_prism_local_files_format_extension",
        monkeypatch,
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    _, file_maps, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)

    assert len(errs) == 1
    error = errs[0]
    assert isinstance(error, prism.ParsingException)
    assert (
        str(error) == "Expected .csv for 'local_file_col_name' but got '.xlsx' instead."
    )

    [upload] = file_maps
    assert upload.gs_key == "1/artifact.csv"


def test_prism_local_files_format_multiple_extensions(monkeypatch):
    """ Tests prism ability to gcs_uri """

    mock_XlTemplateReader_from_excel(
        {
            "files": [
                ["#header", "record", "local_file_col_name"],
                ["#data", "1", "somewhere/on/my/computer.tif"],
                ["#data", "2", "somewhere/on/my/computer.tiff"],
                ["#data", "3", "somewhere/on/my/computer.NONtiff"],
                ["#data", "4", "somewhere/on/my/computer.svs"],
                ["#data", "5", "somewhere/on/my/computer.qptiff"],
            ]
        },
        monkeypatch,
    )

    error_str = (
        "Bad file type {val!r}. It should be in one of .tiff .tif .qptiff .svs formats"
    )

    template = build_mock_Template(
        {
            "$id": "test_files",
            "title": "files",
            "prism_template_root_object_schema": "test_schema.json",
            "properties": {
                "worksheets": {
                    "files": {
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
                                        "check_errors": (
                                            "lambda val: f'%s' if val.rsplit('.', 1)[-1] not in ['svs', 'tiff', 'tif', 'qptiff'] else None"
                                            % error_str
                                        ),
                                        "template_comment": "In one of .tiff .tif .qptiff .svs formats.",
                                    },
                                    "is_artifact": 1,
                                    "type_ref": "test_schema.json#/definitions/file_path",
                                },
                            }
                        },
                    }
                }
            },
        },
        "test_prism_local_files_format_extension",
        monkeypatch,
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    _, file_maps, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)

    assert len(errs) == 1
    error = errs[0]
    assert isinstance(error, prism.ParsingException)
    assert str(error) == error_str.format(val="somewhere/on/my/computer.NONtiff")

    assert len(file_maps) == 4
    expected_extensions = ["tif", "tiff", "svs", "qptiff"]
    # check that we have only "proper" (checked by `check_errors`) extensions
    local_extensions = [util.get_file_ext(fm.local_path) for fm in file_maps]
    gcs_extensions = [util.get_file_ext(fm.gs_key) for fm in file_maps]
    assert expected_extensions == gcs_extensions == local_extensions


def _tab_joining_template_schema() -> dict:
    author_pointer = "test_schema.json#definitions/author%s"
    book_pointer = author_pointer % "/properties/books/items%s"

    return {
        "$id": "test_joining",
        "title": "authors and books",
        "prism_template_root_object_schema": "test_schema.json",
        "properties": {
            "worksheets": {
                "authors": {
                    "prism_preamble_object_pointer": "#",
                    "prism_data_object_pointer": "/authors/0/books/0",
                    "preamble_rows": {},
                    "data_columns": {
                        "Authors": {
                            "author id": {
                                "merge_pointer": "2/author_id",
                                "type_ref": author_pointer % "/properties/author_id",
                            },
                            "author name": {
                                "merge_pointer": "2/author_name",
                                "type_ref": author_pointer % "/properties/author_name",
                            },
                        }
                    },
                },
                "books": {
                    "prism_preamble_object_pointer": "#",
                    "prism_data_object_pointer": "/authors/0/books/0",
                    "preamble_rows": {},
                    "data_columns": {
                        "Books": {
                            "book id": {
                                "merge_pointer": "/book_id",
                                "type_ref": book_pointer % "/properties/book_id",
                                "process_as": [
                                    {
                                        "merge_pointer": "2/author_id",
                                        "parse_through": "lambda x: x[:4]",
                                        "type_ref": (
                                            author_pointer % "/properties/author_id"
                                        ),
                                    }
                                ],
                            },
                            "book name": {
                                "merge_pointer": "/book_name",
                                "type_ref": book_pointer % "/properties/book_name",
                            },
                        }
                    },
                },
            }
        },
    }


def test_prism_joining_tabs(monkeypatch):
    """ Tests whether prism can join data from two excel tabs for a shared metadata subtree """

    mock_XlTemplateReader_from_excel(
        {
            "authors": [
                ["#header", "author id", "author name"],
                ["#data", "CPP0", "Alice"],
                ["#data", "CPP1", "Bob"],
            ],
            "books": [
                ["#header", "book id", "book name"],
                ["#data", "CPP1S0.00", "Foo"],
                ["#data", "CPP1S1.00", "Bar"],
                ["#data", "CPP0S0.00", "Baz"],
                ["#data", "CPP0S1.00", "Buz"],
            ],
        },
        monkeypatch,
    )

    template = build_mock_Template(
        _tab_joining_template_schema(), "test_prism_joining_tabs", monkeypatch
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    patch, file_maps, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)
    assert len(errs) == 0
    assert len(file_maps) == 0

    assert patch == {
        "authors": [
            {
                "books": [
                    {"book_id": "CPP0S0.00", "book_name": "Baz"},
                    {"book_id": "CPP0S1.00", "book_name": "Buz"},
                ],
                "author_id": "CPP0",
                "author_name": "Alice",
            },
            {
                "books": [
                    {"book_id": "CPP1S0.00", "book_name": "Foo"},
                    {"book_id": "CPP1S1.00", "book_name": "Bar"},
                ],
                "author_id": "CPP1",
                "author_name": "Bob",
            },
        ]
    }


def test_prism_process_as_error(monkeypatch):
    """Tests that prismify doesn't crash when a `parse_through` function errors"""
    mock_XlTemplateReader_from_excel(
        {
            "authors": [["#header", "author id"], ["#data", "CPP0"]],
            "books": [["#header", "book id", "book name"], ["#data", None, 100]],
        },
        monkeypatch,
    )

    template = build_mock_Template(
        _tab_joining_template_schema(), "test_prism_process_as", monkeypatch
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    _, _, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)
    assert str(errs[0]).startswith("Cannot extract author_id from book id value: None")


def test_parse_through_basic(monkeypatch):
    """Checks prismify directive "parse_through" """

    mock_XlTemplateReader_from_excel(
        {"ws1": [["#preamble", "propname", "propval"]]}, monkeypatch
    )
    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    template_schema = {
        "title": "parse_through",
        "prism_template_root_object_schema": "test_schema.json",
        "properties": {
            "worksheets": {
                "ws1": {
                    "prism_preamble_object_schema": "test_schema.json",
                    "prism_preamble_object_pointer": "#",
                    "prism_data_object_pointer": "/whatever",
                    "preamble_rows": {
                        "propname": {
                            "type": "string",
                            "parse_through": "lambda x: f'encrypted({x})'",
                            "merge_pointer": "/propname",
                        }
                    },
                }
            }
        },
    }
    template = build_mock_Template(template_schema, "test_template_name", monkeypatch)

    patch, _, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)
    assert not errs

    assert patch == {"propname": "encrypted(propval)"}

    # Check working with null/None values"""

    mock_XlTemplateReader_from_excel(
        {"ws1": [["#preamble", "propname", None]]}, monkeypatch
    )
    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    template_schema["properties"]["worksheets"]["ws1"]["preamble_rows"]["propname"][
        "allow_empty"
    ] = True
    template = build_mock_Template(template_schema, "test_template_name", monkeypatch)

    patch, _, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)
    assert not errs

    # empty val (None) was not parsed through
    assert patch != {"propname": "encrypted(None)"}
    # but was skipped all together
    assert patch == {}


# TODO rename to "allow_None"
def test_allow_empty(monkeypatch):
    """Check "allow_empty" skips None values"""

    mock_XlTemplateReader_from_excel(
        {"ws1": [["#preamble", "id", "id"], ["#preamble", "prop", None]]}, monkeypatch
    )
    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    template = build_mock_Template(
        {
            "title": "parse_through",
            "prism_template_root_object_schema": "test_schema.json",
            "properties": {
                "worksheets": {
                    "ws1": {
                        "prism_preamble_object_schema": "test_schema.json",
                        "prism_preamble_object_pointer": "#",
                        "prism_data_object_pointer": "/whatever",
                        "preamble_rows": {
                            "id": {"type": "string", "merge_pointer": "/id"},
                            "prop": {
                                "type": "string",
                                "merge_pointer": "/prop",
                                "allow_empty": True,
                            },
                        },
                    }
                }
            },
        },
        "test_preamble_parsing_error",
        monkeypatch,
    )

    _, _, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)

    patch, _, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)
    assert not errs

    assert patch == {"id": "id"}


def test_confilicting_values_in_one_template(monkeypatch):
    """ Tests that prismify doesn't allow two different values for some property """
    mock_XlTemplateReader_from_excel(
        {
            "authors": [
                ["#header", "author id", "author name"],
                ["#data", "auth 1", "my name is"],
                ["#data", "auth 1", "slim shady"],
            ]
        },
        monkeypatch,
    )

    template = build_mock_Template(
        {
            "$id": "test_value_conflict_override",
            "title": "authors",
            "prism_template_root_object_schema": "test_schema.json",
            "properties": {
                "worksheets": {
                    "authors": {
                        "prism_preamble_object_pointer": "#",
                        "prism_data_object_pointer": "/authors/0",
                        "preamble_rows": {},
                        "data_columns": {
                            "Authors": {
                                "author id": {
                                    "merge_pointer": "/author_id",
                                    "type": "string",
                                },
                                "author name": {
                                    "merge_pointer": "/author_name",
                                    "type": "string",
                                },
                            }
                        },
                    }
                }
            },
        },
        "test_prism_process_as",
        monkeypatch,
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    _, _, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)
    assert len(errs) == 1
    err_msg = str(errs[0])
    assert "slim shady" in err_msg
    assert "my name is" in err_msg
    assert "author_id='auth 1'" in err_msg
    assert "row=3 worksheet='authors'" in err_msg


def test_prism_do_not_merge(monkeypatch):
    """ Tests whether prism acknowledges do_not_merge """

    mock_XlTemplateReader_from_excel(
        {"analysis": [["#header", "id", "comment"], ["#data", "111", "whatever"]]},
        monkeypatch,
    )

    template = Template(
        {
            "properties": {
                "worksheets": {
                    "analysis": {
                        "prism_data_object_pointer": "/authors/-",
                        "data_columns": {
                            "section name": {
                                "id": {
                                    "merge_pointer": "/author_id",  # so proper mergeStrategy kicks in
                                    "type": "string",
                                },
                                "comment": {
                                    "do_not_merge": True,
                                    "type": "string",
                                    "process_as": [
                                        {
                                            "parse_through": "lambda comment: f'{comment}_some_path.txt'",
                                            "merge_pointer": "/artifact",
                                            "gcs_uri_format": "{id}/artifact.txt",
                                            "type_ref": "assays/components/local_file.json#properties/file_path",
                                            "is_artifact": 1,
                                        }
                                    ],
                                },
                            }
                        },
                    }
                }
            }
        },
        "test_prism_do_not_merge",
    )

    monkeypatch.setattr(
        "cidc_schemas.prism.core.SUPPORTED_TEMPLATES", ["test_prism_do_not_merge"]
    )

    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert not errs

    patch, file_maps, errs = core.prismify(xlsx, template)
    assert len(errs) == 0

    patch["authors"][0]["artifact"]["upload_placeholder"] = "123"

    assert patch == {
        "authors": [
            {
                "author_id": "111",
                "artifact": {
                    "upload_placeholder": "123",
                    "facet_group": "/artifact.txt",
                },
            }
        ]
    }


def test_prism_many_artifacts_from_process_as_on_one_record(monkeypatch):
    """ Tests whether prism can extract many file_map entries from process_as on one record """

    mock_XlTemplateReader_from_excel(
        {
            "groups": [
                ["#header", "group_id", "left_id", "right_id"],
                ["#data", "000", "sid1_0", "sid2_0"],
                ["#data", "111", "sid1_1", "sid2_1"],
            ]
        },
        monkeypatch,
    )

    template = build_mock_Template(
        {
            "$id": "test_analysis",
            "title": "...",
            "prism_template_root_object_schema": "test_schema.json",
            "properties": {
                "worksheets": {
                    "groups": {
                        "prism_data_object_pointer": "/groups/-",
                        "preamble_rows": {},
                        "data_columns": {
                            "groups": {
                                "group_id": {
                                    "merge_pointer": "/group_id",
                                    "type": "string",
                                    "process_as": [
                                        {
                                            "parse_through": "lambda x: f'group/{x}_summary.txt'",
                                            "merge_pointer": "/group_txt_file",
                                            "gcs_uri_format": "group/{group_id}/summary.txt",
                                            "type_ref": "test_schema.json#/definitions/file_path",
                                            "is_artifact": 1,
                                        },
                                        {
                                            "parse_through": "lambda x: f'group/{x}_summary.csv'",
                                            "merge_pointer": "/group_csv_file",
                                            "gcs_uri_format": "group/{group_id}/summary.csv",
                                            "type_ref": "test_schema.json#/definitions/file_path",
                                            "is_artifact": 1,
                                        },
                                    ],
                                },
                                "left_id": {
                                    "merge_pointer": "/left_subgroup/left_id",
                                    "type": "string",
                                    "process_as": [
                                        {
                                            "parse_through": "lambda x: f'group/left_subgroup/{x}.txt'",
                                            "merge_pointer": "/left_subgroup/left_txt_file",
                                            "gcs_uri_format": "group/{group_id}/left_subgroup/{left_id}.txt",
                                            "type_ref": "test_schema.json#/definitions/file_path",
                                            "is_artifact": 1,
                                        },
                                        {
                                            "parse_through": "lambda x: f'group/left_subgroup/{x}.csv'",
                                            "merge_pointer": "/left_subgroup/left_csv_file",
                                            "gcs_uri_format": "group/{group_id}/left_subgroup/{left_id}.csv",
                                            "type_ref": "test_schema.json#/definitions/file_path",
                                            "is_artifact": 1,
                                        },
                                    ],
                                },
                                "right_id": {
                                    "merge_pointer": "/right_subgroup/right_id",
                                    "type": "string",
                                    "process_as": [
                                        {
                                            "parse_through": "lambda x: f'group/right_subgroup/{x}.txt'",
                                            "merge_pointer": "/right_subgroup/right_txt_file",
                                            "gcs_uri_format": "group/{group_id}/right_subgroup/{right_id}.txt",
                                            "type_ref": "test_schema.json#/definitions/file_path",
                                            "is_artifact": 1,
                                        },
                                        {
                                            "parse_through": "lambda x: f'group/right_subgroup/{x}.csv'",
                                            "merge_pointer": "/right_subgroup/right_csv_file",
                                            "gcs_uri_format": "group/{group_id}/right_subgroup/{right_id}.csv",
                                            "type_ref": "test_schema.json#/definitions/file_path",
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
        monkeypatch,
    )
    xlsx, errs = XlTemplateReader.from_excel("workbook")
    assert len(errs) == 0

    patch, file_maps, errs = core.prismify(xlsx, template, TEST_SCHEMA_DIR)
    assert len(errs) == 0

    local_paths = [e.local_path for e in file_maps]
    upload_uuids = [e.upload_placeholder for e in file_maps]

    assert 3 * 2 * 2 == len(
        file_maps
    )  # (3 files * 2 fields from each record) * 2 records
    assert 3 * 2 * 2 == len(
        set(upload_uuids)
    )  # (3 files * 2 fields from each record) * 2 records

    assert local_paths != upload_uuids

    assert 2 == len(patch["groups"])

    group_uuids = [
        art["upload_placeholder"]
        for group in patch["groups"]
        for art in group.values()
        if "upload_placeholder" in art
    ]

    subgroup_uuids = [
        v["upload_placeholder"]
        for group in patch["groups"]
        for subgroup in group.values()
        if isinstance(subgroup, dict)
        for v in subgroup.values()
        if "upload_placeholder" in v
    ]

    json_uuids = group_uuids + subgroup_uuids

    assert len(upload_uuids) == len(json_uuids)
    assert set(upload_uuids) == set(json_uuids)


#### END PRISMIFY TESTS ####
