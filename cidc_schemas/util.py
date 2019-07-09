import os
import json
import yaml

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
