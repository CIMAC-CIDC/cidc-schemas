"""Parsers for extracting extra metadata from files containing molecular data."""
import re
from typing import BinaryIO

import openpyxl

from ..json_validation import load_and_validate_schema

# Build a regex from the CIMAC ID pattern in the schema
cimac_id_regex = re.compile(
    load_and_validate_schema("sample.json")["properties"]["cimac_id"]["pattern"]
)


def parse_elisa(xlsx: BinaryIO) -> dict:
    """
    Parses the given ELISA grand serology results file to extract a list of sample IDs.
    If the file is not valid NPX but still xlsx the function will
    return a dict containing an empty list. Sample IDs not conforming to the CIMAC ID
    format will be skipped. The function will pass along any IO errors.
    Args:
        xlsx: an opened NPX file
    Returns:
        arg1: a dict of containing list of sample IDs and number of samples
    """

    # load the file
    if type(xlsx) == str:
        raise TypeError(f"parse_npx only accepts BinaryIO and not file paths")

    workbook = openpyxl.load_workbook(xlsx)

    # extract data to python
    ids = []
    worksheet = workbook[workbook.sheetnames[0]]

    for i, row in enumerate(worksheet.iter_rows()):

        if i == 0:
            assert "CIMAC ID" == row[0].value
            continue

        val = row[0].value

        if val:
            if cimac_id_regex.match(val):
                ids.append(val)

    sample_count = len(ids)

    samples = {"samples": ids, "number_of_samples": sample_count}

    return samples


def parse_npx(xlsx: BinaryIO) -> dict:
    """
    Parses the given NPX file from olink to extract a list of sample IDs.
    If the file is not valid NPX but still xlsx the function will
    return a dict containing an empty list. Sample IDs not conforming to the CIMAC ID
    format will be skipped. The function will pass along any IO errors.
    Args:
        xlsx: an opened NPX file
    Returns:
        arg1: a dict of containing list of sample IDs and number of samples
    """

    # load the file
    if type(xlsx) == str:
        raise TypeError(f"parse_npx only accepts BinaryIO and not file paths")

    workbook = openpyxl.load_workbook(xlsx)

    # extract data to python
    ids = []
    for worksheet_name in workbook.sheetnames:

        # simplify.
        worksheet = workbook[worksheet_name]
        seen_onlinkid = False
        for i, row in enumerate(worksheet.iter_rows()):

            # extract values from row
            vals = [col.value for col in row]

            first_cell = vals[0]

            # skip empty
            if len(vals) == 0 or first_cell is None:
                continue

            # check if we are starting ids
            if first_cell == "OlinkID":
                seen_onlinkid = True
                continue

            # check if we are done.
            if first_cell == "LOD":
                break

            # get the identifier
            if seen_onlinkid:
                # check that it is a CIMAC ID
                if cimac_id_regex.match(first_cell):
                    ids.append(first_cell)

    sample_count = len(ids)

    samples = {"samples": ids, "number_of_samples": sample_count}

    return samples


EXTRA_METADATA_PARSERS = {"olink": parse_npx, "elisa": parse_elisa}
