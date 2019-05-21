import os
import json
from typing import List

import jinja2

from cidc_schemas.json_validation import load_and_validate_schema

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(DOCS_DIR, '..')
TEMPLATES_DIR = os.path.join(DOCS_DIR, 'templates')
HTML_DIR = os.path.join(DOCS_DIR, "docs")


def get_schemas() -> List[dict]:
    """Load all JSON schemas"""
    schemas = []
    schemas_dir = os.path.join(ROOT_DIR, "schemas")
    for root, _, paths in os.walk(schemas_dir):
        for path in paths:
            schema_path = os.path.join(root, path)
            schema = load_and_validate_schema(schema_path, schemas_dir)
            schemas.append(schema)

    return schemas


def extract_properties(properties, property_dict, required):
    """Extract Properties"""

    # loop over properties
    for current_property in properties:
        target_property = {}
        target_property["description"] = properties[current_property]["description"].replace(
            "'", "")
        target_property["type"] = properties[current_property]["type"]
        try:
            target_property["format"] = properties[current_property]["format"]
        except KeyError:
            target_property["format"] = ""

        try:
            if current_property in required:
                required_property = "[Required]"
            else:
                required_property = "[Optional]"
            target_property["required"] = required_property
        except KeyError:
            target_property["required"] = "[Optional]"

        try:
            item_list = properties[current_property]["enum"]
            target_property["enum"] = item_list
        except KeyError:
            try:
                item_list = properties[current_property]["items"]["enum"]
                target_property["enum"] = item_list
            except KeyError:
                target_property["enum"] = []
        property_dict[current_property] = target_property


def process_entity(entity: dict, template_env: jinja2.Environment, property_dict: dict) -> dict:
    """Create HTML for the Specified Entity"""

    # find required properties
    req_props: dict = {}
    if 'required' in entity:
        req_props = entity['required']

    properties = entity["properties"]
    extract_properties(properties, property_dict, req_props)
    sorted_property_list = sorted(properties)

    template = template_env.get_template("entity.html")
    rendered_template = template.render(schema=entity,
                                        properties=properties,
                                        sorted_property_list=sorted_property_list,
                                        property_dict=property_dict)

    entity_name = (entity.get('id') or entity.get('$id'))
    print("Creating:  %s.html" % entity_name)
    with open("%s/%s.html" % (HTML_DIR, entity_name), "w") as f:
        f.write(rendered_template)

    return entity


def process_template(manifest_name, entity_json_set, property_dict, column_descriptions, template_env):
    """Create HTML for the Specified Template"""
    file_name = os.path.join("manifests", manifest_name,
                             "%s.json" % manifest_name)
    entity = get_json(file_name)

    template = template_env.get_template("manifest.html")
    output_text = template.render(schema=entity,
                                  entity_json_set=entity_json_set,
                                  property_dict=property_dict,
                                  column_descriptions=column_descriptions)
    print("Creating:  %s.html" % manifest_name)
    fd = open("%s/%s.html" % (HTML_DIR, manifest_name), "w")
    fd.write(output_text)
    fd.close()
    return entity


def generate_docs():
    templateLoader = jinja2.FileSystemLoader(TEMPLATES_DIR)
    templateEnv = jinja2.Environment(loader=templateLoader)
    property_dict = {}

    # Create HTML Pages for Each Entity
    entity_list = []
    entity_list.append("clinical_trial")
    entity_list.append("participant")
    entity_list.append("sample")
    entity_list.append("aliquot")
    entity_list.append("user")
    entity_list.append("artifact")
    entity_list.append("wes_artifact")
    entity_list.append("shipping_core")
    entity_json_set = {}
    for entity in entity_list:
        entity_json_set[entity] = (process_entity(
            entity, templateEnv, property_dict))

    # Create HTML Pages for Each Manifest
    column_descriptions = {}
    column_descriptions["core_columns"] = "Core Columns:  Manifest Header"
    column_descriptions["shipping_columns"] = "Shipping Columns:  Completed by the BioBank"
    column_descriptions["receiving_columns"] = "Receiving Columns:  Completed by the CIMAC"

    manifest_list = []
    manifest_list.append("pbmc")
    manifest_json_set = {}
    for manifest in manifest_list:
        manifest_json_set[manifest] = process_template(manifest, entity_json_set,
                                                       property_dict, column_descriptions, templateEnv)

    # Create the Index Page
    template = templateEnv.get_template("index.html")
    print("Creating index.html")
    outputText = template.render(entity_list=entity_list, entity_json_set=entity_json_set,
                                 manifest_list=manifest_list, manifest_json_set=manifest_json_set)
    fd = open("%s/index.html" % HTML_DIR, "w")
    fd.write(outputText)
    fd.close()


if __name__ == '__main__':
    generate_docs()
