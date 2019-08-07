"""Methods for working with shipping/receiving manifests"""

import os
import logging

from .template import Template
from .constants import MANIFEST_DIR

logger = logging.getLogger('cidc_schemas.manifest')


def generate_empty_manifest(schema_path: str, target_path: str):
    """Write the .xlsx shipping/receiving manifest for the given schema to the target path."""
    logger.info(f"Writing empty manifest for {schema_path} to {target_path}.")
    template = Template.from_json(schema_path)
    template.to_excel(target_path)


def generate_all_manifests(target_dir: str):
    """
    Generate empty manifest .xlsx files for every available manifest schema and 
    write them to the target directory.
    """
    for manifest_schema_file in os.listdir(MANIFEST_DIR):
        schema_path = os.path.join(MANIFEST_DIR, manifest_schema_file)
        manifest_xlsx_file = manifest_schema_file.replace('.json', '.xlsx')
        target_path = os.path.join(target_dir, manifest_xlsx_file)
        generate_empty_manifest(schema_path, target_path)
