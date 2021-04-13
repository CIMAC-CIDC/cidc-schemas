"""Parsers for extracting extra metadata from files containing molecular data."""
import re
from typing import BinaryIO

import openpyxl

from ..json_validation import load_and_validate_schema

# Build a regex from the CIMAC ID pattern in the schema
cimac_id_regex = re.compile(
    load_and_validate_schema("sample.json")["properties"]["cimac_id"]["pattern"]
)
cimac_partid_regex = re.compile(
    load_and_validate_schema("participant.json")["properties"]["cimac_participant_id"][
        "pattern"
    ]
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

    idx = 0
    for i, row in enumerate(worksheet.iter_rows()):
        if i == 0:
            # find the one that looks like CIMAC ID
            # ignore case, switch underscores to spaces
            values = [
                str(i.value).upper().strip().replace("_", " ") if str(i.value) else ""
                for i in row
            ]
            assert any(["CIMAC ID" == i for i in values])
            idx = values.index("CIMAC ID")
            continue

        val = row[idx].value

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
    Raises:
        TypeError if xlsx is not a BinaryIO
        ValueError if the second row doesn't start with "NPX data"
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

            if not seen_onlinkid:
                # check that this is actually an NPX file
                if i == 1 and first_cell != "NPX data":
                    raise ValueError("parse_npx got a file that is not in NPX format")

                # check if we are starting ids
                elif first_cell == "OlinkID":
                    seen_onlinkid = True
                    continue

            else:
                # check if we are done.
                if first_cell == "LOD":
                    break

                # get the identifier
                # check that it is a CIMAC ID
                if cimac_id_regex.match(first_cell):
                    ids.append(first_cell)

    sample_count = len(ids)

    samples = {"samples": ids, "number_of_samples": sample_count}

    return samples


def parse_clinical(xlsx: BinaryIO) -> dict:
    """
    Parses the given clinical file to extract a list of participant IDs.
    By convention the first column should be "cimac_part_id" for files containing
    clinical data keyed to a specific participant. All tabs in each XLSX need to be checked
    however some tabs may contain supporting information so not having cimac_part_id is OK.
    Additionally some entire files may contain supporting information so not having any
    cimac_part_id is also OK.

    Also clinical data may contain information for particpants with no CIMAC IDs. For now
    these are simply skipped in our counting.

    Args:
        xlsx: an opened clinical data xlsx file
    Returns:
        arg1: a dict of containing list of participant IDs and number of participants
    Raises:
        TypeError if xlsx is not a BinaryIO
    """

    # load the file
    if type(xlsx) == str:
        raise TypeError(f"parse_clinical only accepts BinaryIO and not file paths")

    workbook = openpyxl.load_workbook(xlsx)

    # extract data to python
    ids = set()
    for worksheet_name in workbook.sheetnames:

        # simplify.
        worksheet = workbook[worksheet_name]
        seen_partid = False
        for i, row in enumerate(worksheet.iter_rows()):

            # extract values from row
            vals = [col.value for col in row]

            # skip empty 1
            if len(vals) == 0:
                continue

            # simplify
            first_cell = vals[0]

            # does this file have cimac_part_id?
            if not seen_partid and first_cell == "cimac_part_id":
                seen_partid = True
                continue

            # some participant ID's might be blank for
            # participants not in the system already (skip these for now)
            if first_cell == "" or not first_cell:
                continue

            # get the identifier
            # check that it is a CIMAC PART ID
            try:
                if cimac_partid_regex.match(first_cell):
                    ids.add(first_cell)
            except TypeError as e:
                continue

    part_count = len(ids)

    parts = {"participants": list(ids), "number_of_participants": part_count}

    return parts


EXTRA_METADATA_PARSERS = {
    "olink": parse_npx,
    "elisa": parse_elisa,
    "clinical_data": parse_clinical,
}
