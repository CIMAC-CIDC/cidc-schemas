import os
from io import BytesIO
from typing import BinaryIO
from zipfile import BadZipFile

import pytest

from cidc_schemas.prism.extra_metadata import parse_elisa, parse_npx

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

# ELISA file and metadata
elisa_file_path = os.path.join(TEST_DATA_DIR, "elisa_test_file.xlsx")
elisa_metadata = {
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
        (parse_elisa, elisa_file_path, elisa_metadata),
    ],
)
def test_parser_smoketest(parser, file_path, target):
    """Check that the parser produces the expected output on a friendly input"""
    with open(file_path, "rb") as f:
        assert parser(f) == target
