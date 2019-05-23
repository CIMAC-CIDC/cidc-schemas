import os
import json
from typing import List, Dict

import jinja2

from cidc_schemas.json_validation import load_and_validate_schema

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(DOCS_DIR, '..')
TEMPLATES_DIR = os.path.join(DOCS_DIR, 'templates')
SCHEMAS_DIR = os.path.join(ROOT_DIR, "schemas")
HTML_DIR = os.path.join(DOCS_DIR, "docs")
PATH_PREFIX = "schemas"


def load_schemas() -> dict:
    """
    Load all JSON schemas into a dictionary keyed on the
    schema directory. Values are dictionaries mapping entity
    names to loaded and validated entity schemas.
    """
    schemas = {}
    for root, _, paths in os.walk(SCHEMAS_DIR):
        root_schemas = {}
        for path in paths:
            schema_path = os.path.join(root, path)

            def json_to_html(ref):
                """Update refs to refer to the URL of the corresponding documentation."""
                url = ref.replace('.json', '.html')
                url = url.replace('properties/', '')
                url = url.replace('definitions/', '')
                url = url.replace('/', '.')
                return {'url': url}

            schema = load_and_validate_schema(
                schema_path, SCHEMAS_DIR, on_refs=json_to_html)

            schema_path = path.replace(".json", ".html").replace("/", ".")
            root_schemas[schema_path] = schema
        relative_root = root.replace(f"{ROOT_DIR}/", "").replace("/", ".")
        schemas[relative_root] = root_schemas

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


def generate_docs():
    templateLoader = jinja2.FileSystemLoader(TEMPLATES_DIR)
    templateEnv = jinja2.Environment(loader=templateLoader)

    # Generate index template
    schemas = load_schemas()
    index_template = templateEnv.get_template('index.j2')
    index_html = index_template.render(schema_directories=schemas)
    with open(os.path.join(HTML_DIR, 'index.html'), 'w') as f:
        f.write(index_html)

    entity_template = templateEnv.get_template('entity.j2')
    template_template = templateEnv.get_template('template.j2')
    template_schemas_path = f'{PATH_PREFIX}.templates'
    for directory, entity in schemas.items():
        # Determine whether these are spreadsheet templates or normal entities
        if directory == template_schemas_path:
            template = template_template
        else:
            template = entity_template

        # Generate the templates
        for name, schema in entity.items():
            entity_html = template.render(
                name=name, schema=schema, scope=directory)
            file_name = f'{directory}.{name}'
            with open(os.path.join(HTML_DIR, file_name), 'w') as f:
                f.write(entity_html)


if __name__ == '__main__':
    generate_docs()
