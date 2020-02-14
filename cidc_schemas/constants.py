import os

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")
METASCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "metaschema", "strict_meta_schema.json"
)
SCHEMA_LIST = [
    f"{d}/{f}".replace(f"{SCHEMA_DIR}/", "")
    for d, _, fs in os.walk(SCHEMA_DIR)
    for f in fs
]

TEMPLATE_DIR = os.path.join(SCHEMA_DIR, "templates")
MANIFEST_DIR = os.path.join(TEMPLATE_DIR, "manifests")
METADATA_DIR = os.path.join(TEMPLATE_DIR, "metadata")
