from .manifest_data import (
    plasma,
    pbmc,
    tissue_slide,
    normal_blood_dna,
    normal_tissue_dna,
    tumor_tissue_dna,
    h_and_e,
)
from .assay_data import wes_bam, wes_fastq, rna_bam, rna_fastq, olink, elisa, cytof, ihc
from .analysis_data import wes_analysis, cytof_analysis
from .utils import PrismTestData, get_test_trial


def list_test_data():
    yield plasma()
    yield pbmc()
    yield tissue_slide()
    yield normal_blood_dna()
    yield normal_tissue_dna()
    yield tumor_tissue_dna()
    yield h_and_e()

    yield wes_bam()
    yield wes_fastq()
    yield rna_bam()
    yield rna_fastq()
    yield olink()
    yield elisa()
    yield cytof()
    yield ihc()

    yield wes_analysis()
    yield cytof_analysis()
