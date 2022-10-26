#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for artifact schemas"""

import os
import pytest
import jsonschema
from cidc_schemas.json_validation import load_and_validate_schema
from .constants import SCHEMA_DIR

ARTIFACT_OBJ = {
    "artifact_category": "Manifest File",
    "artifact_creator": "DFCI",
    "object_url": "dummy",
    "file_name": "dummy.txt",
    "file_size_bytes": 1,
    "data_format": "FASTA",
    "crc32c_hash": "dummy",
    "uploaded_timestamp": "dummy",
    "uploader": "dummy",
    "uuid": "dummy",
    "visible": True,
}

OLINK_RECORD = {
    "run_date": "1/2/98",
    "run_time": "12:00",
    "instrument": "dummy",
    "fludigm_application_version": "0.2.0",
    "fludigm_application_build": "dummy",
    "chip_barcode": "22129",
    "probe_type": "dummy",
    "passive_reference": "dummy",
    "quality_threshold": 90,
    "baseline_correction": "dummy",
    "number_of_samples": 5,
    "number_of_samples_failed": 4,
    "npx_manager_version": "dummy",
    "files": {"assay_npx": "", "assay_raw_ct": ""},
}

ASSAY_CORE = {"assay_creator": "Mount Sinai"}


def _fetch_validator(name):

    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "assays/%s_assay.json" % name)
    if name == "clinical_data":
        schema_path = os.path.join(SCHEMA_DIR, "%s.json" % name)
    schema = load_and_validate_schema(schema_path, schema_root)

    # create validator assert schemas are valid.
    return jsonschema.Draft7Validator(schema)


def test_wes_fastq():

    # create the ngs object
    ngs_obj = {
        "sequencer_platform": "Illumina - NovaSeq 6000",
        "sequencing_protocol": "Express Somatic Human WES (Deep Coverage) v1.1",
        "library_kit": "Hyper Prep ICE Exome Express: 1.0",
        "paired_end_reads": "Paired",
        "read_length": 200,
        "bait_set": "whole_exome_illumina_coding_v1",
    }
    obj = {**ASSAY_CORE, **ngs_obj}  # merge two dictionaries

    # create the wes object
    r1 = ARTIFACT_OBJ.copy()
    r1["data_format"] = "FASTQ.GZ"
    r2 = ARTIFACT_OBJ.copy()
    r2["data_format"] = "FASTQ.GZ"
    record = {
        "cimac_id": "CTTTPPPSA.00",
        "files": {"r1": [r1], "r2": [r2]},
        "sequencing_date": "...",
        "quality_flag": 1,
    }

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("wes")
    validator.validate(obj)


def test_wes_bam():

    # create the ngs object
    ngs_obj = {
        "sequencer_platform": "Illumina - NovaSeq 6000",
        "sequencing_protocol": "Express Somatic Human WES (Deep Coverage) v1.1",
        "library_kit": "Hyper Prep ICE Exome Express: 1.0",
        "paired_end_reads": "Paired",
        "read_length": 200,
        "bait_set": "whole_exome_illumina_coding_v1",
    }
    obj = {**ASSAY_CORE, **ngs_obj}  # merge two dictionaries

    # create the wes object
    bam = ARTIFACT_OBJ.copy()
    bam["data_format"] = "BAM"
    record = {
        "cimac_id": "CTTTPPPSA.00",
        "files": {"bam": [bam]},
        "sequencing_date": "...",
        "quality_flag": 1,
    }

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("wes")
    validator.validate(obj)


def test_rna_fastq():

    # create the ngs object
    ngs_obj = {
        "sequencer_platform": "Illumina - NovaSeq 6000",
        "paired_end_reads": "Paired",
    }
    obj = {**ASSAY_CORE, **ngs_obj}  # merge two dictionaries

    # add custom entry
    obj["enrichment_method"] = "Ribo minus"
    obj["enrichment_vendor_kit"] = "Agilent"

    # create the rna_expression object
    r1 = ARTIFACT_OBJ.copy()
    r1["data_format"] = "FASTQ.GZ"
    record = {
        "library_yield_ng": 666,
        "dv200": 0.7,
        "rqs": 8,
        "rin": 8,
        "quality_flag": 1,
        "cimac_id": "CTTTPPPSA.00",
        "files": {"r1": [r1], "r2": [r1]},
    }

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("rna")
    validator.validate(obj)


def test_rna_bam():

    # create the ngs object
    ngs_obj = {
        "sequencer_platform": "Illumina - NovaSeq 6000",
        "paired_end_reads": "Paired",
    }
    obj = {**ASSAY_CORE, **ngs_obj}  # merge two dictionaries

    # add custom entry
    obj["enrichment_method"] = "Ribo minus"
    obj["enrichment_vendor_kit"] = "Agilent"

    # create the rna_expression object
    bam = ARTIFACT_OBJ.copy()
    bam["data_format"] = "BAM"
    record = {
        "cimac_id": "CTTTPPPSA.00",
        "library_yield_ng": 666,
        "dv200": 0.7,
        "rqs": 8,
        "rin": 8,
        "quality_flag": 1,
        "files": {"bam": [bam]},
    }

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("rna")
    validator.validate(obj)


def test_tcr_fastq():

    # create the tcr_seq object
    r1 = ARTIFACT_OBJ.copy()
    r1["data_format"] = "FASTQ.GZ"
    sample_sheet = ARTIFACT_OBJ.copy()
    sample_sheet["data_format"] = "CSV"
    record = {
        "cimac_id": "CTTTPPPSA.00",
        "files": {
            "replicates": [
                {
                    "replicate_id": "1A",
                    "r1": [r1],
                    "r2": [r1],
                    "i1": [r1],
                    "i2": [r1],
                    "rna_quantity_ng": 600,
                }
            ]
        },
    }

    # create the ngs object
    ngs_obj = {
        "sequencer_platform": "Illumina - NovaSeq 6000",
        "batch_id": "XYZ",
        "sequencing_run_date": "12/12/20",
        "sample_sheet": sample_sheet,
    }

    obj = {**ASSAY_CORE, **ngs_obj}  # merge two dictionaries

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("tcr")
    validator.validate(obj)


def test_cytof():

    # test artifact sub schema
    schema_root = SCHEMA_DIR
    schema_path = os.path.join(
        SCHEMA_DIR, "assays/cytof_assay_core.json#definitions/input_files"
    )
    schema = load_and_validate_schema(schema_path, schema_root)
    validator = jsonschema.Draft7Validator(schema)

    fcs_1 = ARTIFACT_OBJ.copy()
    fcs_1["data_format"] = "FCS"
    fcs_2 = ARTIFACT_OBJ.copy()
    fcs_2["data_format"] = "FCS"
    fcs_3 = ARTIFACT_OBJ.copy()
    fcs_3["data_format"] = "FCS"
    fcs_4 = ARTIFACT_OBJ.copy()
    fcs_4["data_format"] = "FCS"
    sample_records = {"processed_fcs": fcs_1}
    validator.validate(sample_records)

    # create the cytof object
    cytof_platform = {"instrument": "dummy"}

    # create a cytof antibody object.
    antibodies = [
        {
            "antibody": "CD8",
            "isotope": "dummy",
            "dilution": "dummy",
            "stain_type": "Intracellular",
            "usage": "Analysis Only",
        },
        {
            "antibody": "PD-L1",
            "isotope": "dummy",
            "dilution": "dummy",
            "stain_type": "Intracellular",
            "usage": "Used",
        },
    ]
    cytof_panel = {
        "assay_run_id": "run_1",
        "batch_id": "XYZ",
        "cytof_antibodies": antibodies,
        "source_fcs": [fcs_2, fcs_3],
    }

    obj = {**ASSAY_CORE, **cytof_platform, **cytof_panel}  # merge three dictionaries

    # create the cytof object
    fcs_1 = ARTIFACT_OBJ.copy()
    fcs_1["data_format"] = "FCS"
    fcs_2 = ARTIFACT_OBJ.copy()
    fcs_2["data_format"] = "FCS"
    fcs_3 = ARTIFACT_OBJ.copy()
    fcs_3["data_format"] = "FCS"
    assignment = ARTIFACT_OBJ.copy()
    assignment["data_format"] = "CSV"
    compartment = ARTIFACT_OBJ.copy()
    compartment["data_format"] = "CSV"
    profiling = ARTIFACT_OBJ.copy()
    profiling["data_format"] = "CSV"
    cell_count_assignment = ARTIFACT_OBJ.copy()
    cell_count_assignment["data_format"] = "CSV"
    cell_count_compartment = ARTIFACT_OBJ.copy()
    cell_count_compartment["data_format"] = "CSV"
    cell_count_profiling = ARTIFACT_OBJ.copy()
    cell_count_profiling["data_format"] = "CSV"
    report = ARTIFACT_OBJ.copy()
    report["data_format"] = "ZIP"
    analysis = ARTIFACT_OBJ.copy()
    analysis["data_format"] = "ZIP"
    records = {
        "cimac_id": "CTTTPPPSA.00",
        "input_files": {"processed_fcs": fcs_1},
        "output_files": {
            "fcs_file": fcs_1,
            "assignment": assignment,
            "compartment": compartment,
            "profiling": profiling,
            "cell_counts_assignment": assignment,
            "cell_counts_compartment": compartment,
            "cell_counts_profiling": profiling,
        },
    }

    # add a demo sample-level record.
    obj["records"] = [records]

    # create validator assert schemas are valid.
    validator = _fetch_validator("cytof")
    validator.validate(obj)


def test_ihc():

    # create the IHC object
    ihc_obj = {
        "slide_scanner_model": "Hamamatsu",
        "staining_platform": "auto",
        "autostainer_model": "Bond RX",
    }
    # create the IHC antibody
    antibody = {
        "antibody": "PD-L1",
        "company": "dummy",
        "clone": "dummy",
        "cat_num": "13684",
        "lot_num": "547645",
        "dilution": "1:200",
        "incubation_time": "1 hr",
        "incubation_temp": "RT",
    }
    ihc_obj["antibody"] = antibody

    # merge into ready example.
    obj = {**ASSAY_CORE, **ihc_obj}

    # create the artifact object
    image_1 = ARTIFACT_OBJ.copy()
    image_1["data_format"] = "IMAGE"
    image_1["height"] = 300
    image_1["width"] = 250
    image_1["channels"] = 3
    record = {
        "cimac_id": "CTTTPPPSA.00",
        "marker_positive": "no_call",
        "tumor_proportion_score": 0,
        "h_score": 22,
        "files": {"ihc_image": image_1},
    }

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("ihc")
    validator.validate(obj)


def test_mif():

    # create the mif object
    image = {"slide_scanner_model": "Vectra 2.0"}

    obj = {**ASSAY_CORE, **image}  # merge dictionaries

    # create the artifact object
    image = ARTIFACT_OBJ.copy()
    image["data_format"] = "IMAGE"
    image["height"] = 300
    image["width"] = 250
    image["channels"] = 3
    text = ARTIFACT_OBJ.copy()
    text["data_format"] = "TEXT"
    record = {
        "cimac_id": "CTTTPPPSA.00",
        "files": {
            "regions_of_interest": [
                {
                    "roi_id": "foo",
                    "im3": image,
                    "component_data": image,
                    "composite_image": image,
                    "exports": [
                        {
                            "export_id": "bar",
                            "binary_seg_maps": image,
                            "cell_seg_data": text,
                            "cell_seg_data_summary": text,
                            "phenotype_map": image,
                            "score_data": [text],
                            "score_data": [text],
                        }
                    ],
                }
            ]
        },
    }

    ab = {
        "antibody": "foobar-999",
        "fluor_wavelength": 999,
        "primary_ab_dilution": "1",
        "dilutent": "water",
        "fluor_dilution": "1",
        "antigen_retrieval_time": "00:00:00",
        "primary_incubation_time": "00:00:00",
        "amplification_time": "00:00:00",
    }

    # add a demo record.
    obj["records"] = [record]
    obj["panel"] = "Panel 1: PD-L1, CD68, PD-1, CD8, CD3, pan-cytokeratin, DAPI"
    obj["antibodies"] = [ab]

    # create validator assert schemas are valid.
    validator = _fetch_validator("mif")
    validator.validate(obj)

    # assert negative behaviors
    del obj["records"][0]["files"]["regions_of_interest"][0]["exports"][0][
        "cell_seg_data"
    ]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)


def test_olink():

    # build up the batch object with one record
    npx = ARTIFACT_OBJ.copy()
    npx["data_format"] = "NPX"
    npx["samples"] = ["CTTTPPPS1.00", "CTTTPPPS2.00", "CTTTPPPS3.00"]
    npx["number_of_samples"] = 3
    csv = ARTIFACT_OBJ.copy()
    csv["data_format"] = "CSV"
    record = OLINK_RECORD.copy()
    record["files"]["assay_npx"] = npx
    record["files"]["assay_raw_ct"] = csv
    batch = {
        **ASSAY_CORE,
        "batch_id": "batch1",
        "panel": "panel v1",
        "records": [record],
    }

    # create the olink object
    obj = {
        "batches": [batch],
        "study": {"npx_manager_version": "whatever", "npx_file": npx},
    }

    # create validator assert schemas are valid.
    validator = _fetch_validator("olink")
    validator.validate(obj)

    # assert negative behaviors
    del obj["batches"][0]["records"][0]["number_of_samples"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)


def test_microbiome():

    # create the ngs object
    ngs_obj = {"sequencer_platform": "Illumina - NovaSeq 6000"}
    obj = {**ASSAY_CORE, **ngs_obj}  # merge two dictionaries

    fastq = ARTIFACT_OBJ.copy()
    fastq["data_format"] = "FASTQ.GZ"
    tsv = ARTIFACT_OBJ.copy()
    tsv["data_format"] = "TSV"
    pdf = ARTIFACT_OBJ.copy()
    pdf["data_format"] = "PDF"

    # add custom entry
    obj["batch_id"] = "batch1"
    obj["forward_fastq"] = fastq
    obj["forward_index"] = fastq
    obj["reverse_fastq"] = fastq
    obj["reverse_index"] = fastq
    obj["otu_table"] = tsv
    obj["summary_file"] = pdf

    # create the microbiome object
    record = {
        "library_yield_ng": 666,
        "cimac_id": "CTTTPPPSA.00",
    }

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("microbiome")
    validator.validate(obj)


def test_clinicaldata():

    # create validator
    validator = _fetch_validator("clinical_data")

    # create clinical data that is valid
    tmp = ARTIFACT_OBJ.copy()
    tmp["file_name"] = "dummy.xlsx"
    tmp["data_format"] = "XLSX"
    tmp["participants"] = ["CTTTPPP", "CTTTPPQ", "CTTTPPD"]
    tmp["number_of_participants"] = 3
    clin_dat = {"records": [{"clinical_file": tmp, "comment": "dummyxyz"}]}
    obj = {**ASSAY_CORE, **clin_dat}
    validator.validate(obj)

    # valid without a comment.
    clin_dat = {"records": [{"clinical_file": tmp}]}
    obj = {**ASSAY_CORE, **clin_dat}
    validator.validate(obj)

    # try to validate this (expect failure on filetype)
    tmp = ARTIFACT_OBJ.copy()
    tmp["file_name"] = "dummy.xlsx"
    tmp["participants"] = ["CTTTPPP", "CTTTPPQ", "CTTTPPD"]
    tmp["number_of_participants"] = 3
    clin_dat = {"records": [{"clinical_file": tmp, "comment": "dummyxyz"}]}
    obj = {**ASSAY_CORE, **clin_dat}
    with pytest.raises(jsonschema.ValidationError, match="is not valid"):
        validator.validate(clin_dat)


def test_ctdna():
    # set up BAM and BAI
    bam = ARTIFACT_OBJ.copy()
    bam["data_format"] = "BAM"
    bai = ARTIFACT_OBJ.copy()
    bai["data_format"] = "BAM.BAI"
    pdf = ARTIFACT_OBJ.copy()
    pdf["data_format"] = "PDF"
    zip = ARTIFACT_OBJ.copy()
    zip["data_format"] = "ZIP"

    # create the record
    record = {
        "cimac_id": "CTTTPPPSA.00",
        "demultiplexed_bam": bam,
        "demultiplexed_bam_index": bai,
        "genome-wide_plots": pdf,
        "bias_qc_plots": pdf,
        "optimal_solution": zip,
        "other_solutions": zip,
        "fraction_cna_subclonal": 0.1,
        "fraction_genome_subclonal": 0.2,
        "gc_map_correction_mad": 0.04,
        "subclone_fraction": 0.15,
        "tumor_fraction": 0.25,
        "tumor_ploidy": 2.5,
    }

    # add a demo record.
    obj = ASSAY_CORE.copy()
    obj["batch_id"] = "test_batch"
    obj["summary_plots"] = pdf
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("ctdna")
    validator.validate(obj)


def test_mibi():
    # set up generic artifacts
    tif = ARTIFACT_OBJ.copy()
    tif["data_format"] = "IMAGE"
    csv = ARTIFACT_OBJ.copy()
    csv["data_format"] = "CSV"

    # create the record
    roi = {
        "roi_id": "id",
        "multichannel_image": tif,
        "cluster_labels": tif,
        "channel_names": csv,
        "single_cell_table": csv,
        "roi_description": "foo",
        "comment": "bar",
    }
    record = {"cimac_id": "CTTTPPPSA.00", "regions_of_interest": [roi]}
    ab = {
        "channel_id": "foobar",
        "antibody": "foobar-999",
        "scicrunch_rrid": "rrid",
        "uniprot_accession_number": "uniprot",
        "lot_num": "abc",
        "dilution": "10",
        "concentration_value": 35,
        "concentration_units": "c",
        "cat_num": "999",
        "conjugated_tag": "999",
    }

    # add a demo record.
    obj = ASSAY_CORE.copy()
    obj["antibodies"] = [ab]
    obj["batch_id"] = "foobar"
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("mibi")
    validator.validate(obj)
