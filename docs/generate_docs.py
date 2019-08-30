import os
import jinja2
import json
from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.constants import SCHEMA_DIR

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(DOCS_DIR, '..')
TEMPLATES_DIR = os.path.join(DOCS_DIR, 'templates')
HTML_DIR = os.path.join(DOCS_DIR, "docs")


def load_schemas() -> dict:
    """
    Load all JSON schemas into a dictionary keyed on the
    schema directory. Values are dictionaries mapping entity
    names to loaded and validated entity schemas.
    """
    schemas = {}
    for root, _, paths in os.walk(SCHEMA_DIR):
        root_schemas = {}
        for path in paths:
            schema_path = os.path.join(root, path)

            def json_to_html(ref: str) -> dict:
                """Update refs to refer to the URL of the corresponding documentation."""
                url = ref.replace('.json', '.html')
                url = url.replace('properties/', '')
                url = url.replace('definitions/', '')
                url = url.replace('/', '.')
                return {'url': url}

            full_json = load_and_validate_schema(
                schema_path, SCHEMA_DIR)
            schema = load_and_validate_schema(
                schema_path, SCHEMA_DIR, on_refs=json_to_html)

            assert path.endswith(".json")
            schema_name = path[:-5].replace("/", ".")
            root_schemas[schema_name] = (schema, full_json)

        relative_root = root.replace(SCHEMA_DIR, "").replace("/", ".")
        relative_root = relative_root.replace(".", "", 1)
        schemas[relative_root] = root_schemas

    return schemas


def generate_docs(out_directory: str = HTML_DIR):
    """
    Generate documentation based on the schemas found in `SCHEMA_DIR`.
    """

    # Empty contents of docs/docs directory to prevent old html renders from showing up
    for filename in os.listdir(out_directory):
        os.unlink(out_directory + "/" + filename)

    templateLoader = jinja2.FileSystemLoader(TEMPLATES_DIR)
    templateEnv = jinja2.Environment(loader=templateLoader)

    # Generate index template
    schemas = load_schemas()
    index_template = templateEnv.get_template('index.j2')
    index_html = index_template.render(schema_directories=schemas)
    with open(os.path.join(out_directory, 'index.html'), 'w') as f:
        f.write(index_html)

    entity_template = templateEnv.get_template('entity.j2')
    template_template = templateEnv.get_template('template.j2')

    for directory, entity in schemas.items():

        # Determine whether these are spreadsheet templates or normal entities
        if directory in ('templates.manifests', 'templates.metadata'):
            template = template_template
        else:
            template = entity_template

        # Generate the templates
        for name, (schema, full_json) in entity.items():

            full_name = f'{directory}.{name}'
            if full_name.startswith("."):
                full_name = full_name[1::]

            # render the HTML to string
            entity_html = template.render(
                name=name,
                full_name=full_name,
                schema=schema,
                scope=directory,
                full_json_str=json.dumps(full_json, sort_keys=True, indent=4))

            # write this out
            with open(os.path.join(out_directory, f'{full_name}.html'), 'w') as f:
                f.write(entity_html)


if __name__ == '__main__':
    generate_docs()
