from cidc_schemas.prism.constants import (
    ASSAY_TO_FILEPATH,
    SUPPORTED_ASSAYS,
    SUPPORTED_ANALYSES,
    SUPPORTED_MANIFESTS,
)


def test_assay_to_filepath():
    assert sorted(list(ASSAY_TO_FILEPATH.keys())) == sorted(
        SUPPORTED_ASSAYS + SUPPORTED_ANALYSES + ["participants info", "samples info"]
    )
    assert all(manifest not in ASSAY_TO_FILEPATH for manifest in SUPPORTED_MANIFESTS)
