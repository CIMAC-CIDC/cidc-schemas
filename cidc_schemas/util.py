import os
import json
import yaml
import openpyxl
from typing import Union, BinaryIO


def yaml_to_json(yaml_path: str) -> str:
    """
        Given a path to a yaml file, write the equivalent json
        to a file of the same name and return the new filename.
    """
    filename, ext = yaml_path.rsplit('.', 1)
    assert ext == 'yaml', "expected a yaml file"

    with open(yaml_path, 'r') as stream:
        dictionary = yaml.safe_load(stream)
        json_path = f"{filename}.json"
        with open(json_path, 'w') as new_file:
            json.dump(dictionary, new_file, indent=2)

    return json_path


def json_to_yaml(json_path: str) -> str:
    """
        Given a path to a json file, write the equivalent yaml
        to a file of the same name and return the new filename.
    """
    filename, ext = json_path.rsplit('.', 1)
    assert ext == 'json', "expected a json file"

    with open(json_path, 'r') as stream:
        dictionary = json.load(stream)
        yaml_path = f"{filename}.yaml"
        with open(yaml_path, 'w') as new_file:
            yaml.safe_dump(dictionary, new_file)

    return yaml_path


def parse_npx(xlsx_path: Union[str, BinaryIO]):
    """
        Parses the given NPX file from OLINK
        to extrat a list of aliquot IDs
    """

    # load the file
    workbook = openpyxl.load_workbook(xlsx_path)

    # extract data to python
    ids = []
    for worksheet_name in workbook.sheetnames:

        # simplify.
        worksheet = workbook[worksheet_name]
        header_width = 0
        seen_onlinkid = False
        for i, row in enumerate(worksheet.iter_rows()):

            # Convert to string and extract type annotation
            vals = [col.value for col in row]

            # skip empty
            if vals[0] is None:
                continue

            # check if we are starting ids
            if vals[0] == 'OlinkID':
                seen_onlinkid = True
                continue

            # check if we are done.
            if vals[0] == 'LOD':
                break

            # get the identifier
            if seen_onlinkid:
                ids.append(vals[0])

    return ids
