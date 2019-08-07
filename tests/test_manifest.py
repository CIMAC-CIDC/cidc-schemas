"""Test manifest-related convenience methods."""
import os

from cidc_schemas.template import Template
from cidc_schemas.constants import MANIFEST_DIR
from cidc_schemas.manifest import generate_empty_manifest, generate_all_manifests


def test_generate_empty_manifest(pbmc_schema_path, pbmc_template, tmpdir):
    """Check that generate_empty_manifest generates the correct manifest."""
    # Generate the xlsx file with the convenience method
    target_path = tmpdir.join('pbmc_target.xlsx')
    generate_empty_manifest(pbmc_schema_path, target_path)

    # Generate the xlsx file from the known-good Template instance
    # for comparison
    cmp_path = tmpdir.join('pbmc_truth.xlsx')
    pbmc_template.to_excel(cmp_path)

    # Check that the files have the same contents
    with open(target_path, 'rb') as generated, open(cmp_path, 'rb') as comparison:
        assert generated.read() == comparison.read()


def test_generate_all_manifests(tmpdir):
    """Check that generate_all_manifests appears to, in fact, generate all manifests."""
    generate_all_manifests(tmpdir)

    # Check that the right number of empty templates was generated
    schema_files = os.listdir(MANIFEST_DIR)
    generated_files = os.listdir(tmpdir)
    assert len(schema_files) == len(generated_files)

    # Check that the empty templates have the right names
    generated_filenames = set(f.strip('.xlsx') for f in generated_files)
    schema_filenames = set(f.strip('.json') for f in schema_files)
    assert generated_filenames == schema_filenames
