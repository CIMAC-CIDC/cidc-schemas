"""CIDC schemas-specific constants relevant to prismifying/merging functionality."""

from typing import Dict


PROTOCOL_ID_FIELD_NAME = "protocol_identifier"

SUPPORTED_ASSAYS = [
    "atacseq_fastq",
    "wes_fastq",
    "wes_bam",
    "olink",
    "cytof",
    "ihc",
    "elisa",
    "rna_fastq",
    "rna_bam",
    "mibi",
    "mif",
    "tcr_adaptive",
    "tcr_fastq",
    "hande",
    "nanostring",
    "clinical_data",
    "misc_data",
    "ctdna",
    "microbiome",
]

SUPPORTED_SHIPPING_MANIFESTS = [
    "pbmc",
    "plasma",
    "tissue_slide",
    "normal_blood_dna",
    "normal_tissue_dna",
    "tumor_tissue_dna",
    "tumor_tissue_rna",
    "h_and_e",
    "microbiome_dna",
]
# weird non shipping manifest
SUPPORTED_WEIRD_MANIFESTS = [
    "tumor_normal_pairing",
]
SUPPORTED_MANIFESTS = SUPPORTED_SHIPPING_MANIFESTS + SUPPORTED_WEIRD_MANIFESTS

SUPPORTED_ANALYSES = [
    "atacseq_analysis",
    "cytof_analysis",
    "rna_level1_analysis",
    "tcr_analysis",
    "wes_analysis",
    "wes_tumor_only_analysis",
]

SUPPORTED_TEMPLATES = SUPPORTED_ASSAYS + SUPPORTED_MANIFESTS + SUPPORTED_ANALYSES

# provide a way to get file-path prefix for each upload_type
ASSAY_TO_FILEPATH: Dict[str, str] = {
    # analysis is removed on some
    "atacseq_analysis": "atacseq/",
    "rna_level1_analysis": "rna/",
    "wes_analysis": "wes/",
    "wes_tumor_only_analysis": "wes_tumor_only/",
    # assay specifics removed
    "atacseq_fastq": "atacseq/",
    "rna_bam": "rna/",
    "rna_fastq": "rna/",
    "tcr_adaptive": "tcr/",
    "tcr_fastq": "tcr/",
    "wes_bam": "wes/",
    "wes_fastq": "wes/",
    # special cases
    "clinical_data": "clinical/",
    "participants info": "participants/",
    "samples info": "samples/",
    # invariant
    **{
        k: f"{k}/"
        for k in [
            "cytof_analysis",
            "tcr_analysis",
            "ctdna",
            "cytof",
            "elisa",
            "hande",
            "ihc",
            "microbiome",
            "mibi",
            "mif",
            "misc_data",
            "nanostring",
            "olink",
        ]
    },
}
assert all(
    not prefix1.startswith(prefix2)
    for prefix1 in ASSAY_TO_FILEPATH.values()
    for prefix2 in ASSAY_TO_FILEPATH.values()
    if prefix1 != prefix2
), "Prefix codes may not be overlapping"
