import os

import pytest

from cidc_schemas.prism.extra_metadata import parse_elisa, parse_npx, parse_clinical

from ..constants import TEST_DATA_DIR

# Single NPX file and metadata
npx_file_path = os.path.join(TEST_DATA_DIR, "olink", "olink_assay_1_NPX.xlsx")
single_npx_metadata = {
    "number_of_samples": 4,
    "samples": ["CTTTP01A1.00", "CTTTP02A1.00", "CTTTP03A1.00", "CTTTP04A1.00"],
}

# Combined NPX file and metadata
npx_combined_file_path = os.path.join(
    TEST_DATA_DIR, "olink", "olink_assay_combined.xlsx"
)
combined_npx_metadata = {
    "number_of_samples": 9,
    "samples": [
        "CTTTP01A1.00",
        "CTTTP02A1.00",
        "CTTTP03A1.00",
        "CTTTP04A1.00",
        "CTTTP05A1.00",
        "CTTTP06A1.00",
        "CTTTP07A1.00",
        "CTTTP08A1.00",
        "CTTTP09A1.00",
    ],
}

invalid_npx_file_path = os.path.join(
    TEST_DATA_DIR, "olink", "invalid_olink_assay_1_NPX.xlsx"
)

# ELISA file and metadata
elisa_file_path_1 = os.path.join(TEST_DATA_DIR, "elisa_test_file.1.xlsx")
elisa_file_path_2 = os.path.join(TEST_DATA_DIR, "elisa_test_file.2.xlsx")
elisa_metadata_1 = {
    "number_of_samples": 3,
    "samples": ["CTTTP01A1.00", "CTTTP01A2.00", "CTTTP01A3.00"],
}
elisa_metadata_2 = {
    "number_of_samples": 7,
    "samples": [
        "CTTTP01A1.00",
        "CTTTP01A2.00",
        "CTTTP01A3.00",
        "CTTTP02A1.00",
        "CTTTP02A2.00",
        "CTTTP02A3.00",
        "CTTTP02A4.00",
    ],
}

# CLINCAL file and metadata
clinical_file_path_1_csv = os.path.join(TEST_DATA_DIR, "clinical_test_file.1.csv")
clinical_file_path_2_csv = os.path.join(TEST_DATA_DIR, "clinical_test_file.2.csv")
clinical_file_path_1 = os.path.join(TEST_DATA_DIR, "clinical_test_file.1.xlsx")
clinical_metadata_1 = {
    "number_of_participants": 3,
    "participants": ["CNQAABC", "CNQAABQ", "CNQAABD"],
}

clinical_file_path_2 = os.path.join(TEST_DATA_DIR, "clinical_test_file.2.xlsx")
clinical_metadata_2 = {"number_of_participants": 0, "participants": []}

clinical_file_path_3 = os.path.join(TEST_DATA_DIR, "clinical_test_file.3.xlsx")
clinical_metadata_3 = {
    "number_of_participants": 5,
    "participants": ["CNQAABC", "CNQAABD", "CNQAABQ", "CNQAABY", "CNQAABP"],
}

clinical_docx = os.path.join(TEST_DATA_DIR, "clinical_test_file.docx")


@pytest.mark.parametrize("parser", [parse_elisa, parse_npx])
def test_parse_binaryio_only(parser):
    """Check that the parser doesn't accept a file path as argument"""
    file_path = "some/file/path"
    with pytest.raises(TypeError, match="only accepts BinaryIO and not file paths"):
        parser(file_path)


@pytest.mark.parametrize(
    "parser,file_path,target",
    [
        (parse_npx, npx_file_path, single_npx_metadata),
        (parse_npx, npx_combined_file_path, combined_npx_metadata),
        # differ in column order and capitalization/spacing of cimac_id column
        # testing both to prevent unnecessary assumptions in formatting as this is hand generated
        (parse_elisa, elisa_file_path_1, elisa_metadata_1),
        (parse_elisa, elisa_file_path_2, elisa_metadata_2),
    ],
)
def test_parser_smoketest(parser, file_path, target):
    """Check that the parser produces the expected output on a friendly input"""
    with open(file_path, "rb") as f:
        assert parser(f) == target


def test_parse_npx_exc():
    with pytest.raises(TypeError, match=r"not file paths"):
        parse_npx("str should fail")

    with pytest.raises(ValueError, match=r"not in NPX"):
        with open(invalid_npx_file_path, "rb") as f:
            parse_npx(f)


def test_parse_clinical():
    """test for parsing extra metadata (part_ids) from
    clinical data files"""

    def _check_clin_eq(a, b):
        assert a["number_of_participants"] == b["number_of_participants"]
        assert set(a["participants"]) == set(b["participants"])

    # this tests both multiple tabs and extra info tabs
    clinical_file_path_1 = os.path.join(TEST_DATA_DIR, "clinical_test_file.1.xlsx")
    with open(clinical_file_path_1, "rb") as f:
        data = parse_clinical(f)
        _check_clin_eq(data, clinical_metadata_1)

    # this tests csv parsing
    clinical_file_path_1_csv = os.path.join(TEST_DATA_DIR, "clinical_test_file.1.csv")
    with open(clinical_file_path_1_csv, "rb") as f:
        assert not f.read().startswith(b'"version",')
        f.seek(0)
        data = parse_clinical(f)
        _check_clin_eq(data, clinical_metadata_1)

    # this tests versioned csv parsing
    clinical_file_path_2_csv = os.path.join(TEST_DATA_DIR, "clinical_test_file.2.csv")
    with open(clinical_file_path_2_csv, "rb") as f:
        assert f.read().startswith(b"version,")
        f.seek(0)
        data = parse_clinical(f)
        _check_clin_eq(data, clinical_metadata_1)

    # this tests should be empty
    with open(clinical_file_path_2, "rb") as f:
        data = parse_clinical(f)
        _check_clin_eq(data, clinical_metadata_2)

    # this tests should deal with duplicate participants in tabs
    with open(clinical_file_path_3, "rb") as f:
        data = parse_clinical(f)
        _check_clin_eq(data, clinical_metadata_3)

    # this tests if not xlsx/csv files don't get anything
    with open(clinical_docx, "rb") as f:
        assert parse_clinical(f) == {}

    # this tests a versioned csv containing a BOM
    clinical_file_path_2_bom_csv = os.path.join(
        TEST_DATA_DIR, "clinical_test_file.2.bom.csv"
    )
    with open(clinical_file_path_2_bom_csv, "rb") as f:
        data = parse_clinical(f)
        _check_clin_eq(data, clinical_metadata_1)
