"""CIDC schemas-specific constants relevant to prismifying/merging functionality."""

PROTOCOL_ID_FIELD_NAME = "protocol_identifier"

SUPPORTED_ASSAYS = [
    "wes_fastq",
    "wes_bam",
    "olink",
    "cytof",
    "ihc",
    "elisa",
    "rna_fastq",
    "rna_bam",
    "mif",
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
]
# weird non shipping manifest
SUPPORTED_WEIRD_MANIFESTS = ["tumor_normal_pairing"]
SUPPORTED_MANIFESTS = SUPPORTED_SHIPPING_MANIFESTS + SUPPORTED_WEIRD_MANIFESTS

SUPPORTED_ANALYSES = ["cytof_analysis", "wes_analysis", "rna_level1_analysis"]

SUPPORTED_TEMPLATES = SUPPORTED_ASSAYS + SUPPORTED_MANIFESTS + SUPPORTED_ANALYSES
