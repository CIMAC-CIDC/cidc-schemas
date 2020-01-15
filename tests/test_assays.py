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
    "assay_prefix": "dummy",
    "filetype": "assay",
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
    "panel": "dummy",
    "number_of_samples": 5,
    "number_of_samples_failed": 4,
    "npx_manager_version": "dummy",
    "assay_panel_lot": 90,
    "files": {"assay_npx": "", "assay_raw_ct": "", "study_npx": ""},
}

ASSAY_CORE = {"assay_creator": "DFCI", "assay_creator": "Mount Sinai"}


def _fetch_validator(name):

    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "assays/%s_assay.json" % name)
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


def test_rna_expression():

    # create the ngs object
    ngs_obj = {
        "sequencer_platform": "Illumina - NovaSeq 6000",
        "library_vendor_kit": "KAPA - Hyper Prep",
        "paired_end_reads": "Paired",
        "read_length": 200,
    }
    obj = {**ASSAY_CORE, **ngs_obj}  # merge two dictionaries

    # add custom entry
    obj["enrichment_method"] = "Ribo minus"
    obj["enrichment_vendor_kit"] = "Agilent"

    # create the rna_expression object
    r1 = ARTIFACT_OBJ.copy()
    r1["data_format"] = "FASTQ.GZ"
    rgmf = ARTIFACT_OBJ.copy()
    rgmf["data_format"] = "TEXT"
    rgmf["artifact_category"] = "Assay Artifact from CIMAC"
    record = {
        "enrichment_vendor_lot": "dummy_value",
        "library_kit_lot": "dummy_value",
        "library_prep_date": "01/01/2001",
        "capture_date": "01/01/2001",
        "cimac_id": "CTTTPPPSA.00",
        "input_ng": 666,
        "library_yield_ng": 666,
        "average_insert_size": 200,
        "files": {"r1": [r1], "r2": [r1]},
    }

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("rna_expression")
    validator.validate(obj)


def test_cytof():

    # test artifact sub schema
    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "assays/components/cytof/cytof_input.json")
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
    record = {
        "processed_fcs": fcs_1,
        "source_fcs": [fcs_2, fcs_3],
        "normalized_and_debarcoded_fcs": fcs_4,
    }
    validator.validate(record)

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
        "panel_name": "DFCI default",
        "cytof_antibodies": antibodies,
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
    assignment["separator"] = ","
    assignment["header_row"] = 128
    compartment = ARTIFACT_OBJ.copy()
    compartment["data_format"] = "CSV"
    compartment["separator"] = ","
    compartment["header_row"] = 128
    profiling = ARTIFACT_OBJ.copy()
    profiling["data_format"] = "CSV"
    profiling["separator"] = ","
    profiling["header_row"] = 128
    cell_count_assignment = ARTIFACT_OBJ.copy()
    cell_count_assignment["data_format"] = "CSV"
    cell_count_assignment["separator"] = ","
    cell_count_assignment["header_row"] = 128
    cell_count_compartment = ARTIFACT_OBJ.copy()
    cell_count_compartment["data_format"] = "CSV"
    cell_count_compartment["separator"] = ","
    cell_count_compartment["header_row"] = 128
    cell_count_profiling = ARTIFACT_OBJ.copy()
    cell_count_profiling["data_format"] = "CSV"
    cell_count_profiling["separator"] = ","
    profiling["header_row"] = 128
    report = ARTIFACT_OBJ.copy()
    report["data_format"] = "ZIP"
    analysis = ARTIFACT_OBJ.copy()
    analysis["data_format"] = "ZIP"
    record = {
        "cimac_id": "CTTTPPPSA.00",
        "input_files": {"processed_fcs": fcs_1, "source_fcs": [fcs_2, fcs_3]},
        "output_files": {
            "fcs_file": fcs_1,
            "astrolabe_reports": report,
            "astrolabe_analysis": analysis,
            "assignment": assignment,
            "compartment": compartment,
            "profiling": profiling,
            "cell_counts_assignment": assignment,
            "cell_counts_compartment": compartment,
            "cell_counts_profiling": profiling,
        },
    }

    # add a demo record.
    obj["records"] = [record]

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
    image = {"slide_scanner_model": "Vectra 2.0", "protocol_name": "E4412"}

    imaging_data = {"internal_slide_id": "a1s1e1"}
    obj = {**ASSAY_CORE, **image, **imaging_data}  # merge three dictionaries

    # create the artifact object
    image_1 = ARTIFACT_OBJ.copy()
    image_1["data_format"] = "IMAGE"
    image_1["height"] = 300
    image_1["width"] = 250
    image_1["channels"] = 3
    csv_1 = ARTIFACT_OBJ.copy()
    csv_1["data_format"] = "CSV"
    csv_1["separator"] = ","
    csv_1["header_row"] = 128
    text = ARTIFACT_OBJ.copy()
    text["data_format"] = "TEXT"
    record = {
        "project_inform_folder": "dummy",
        "mif_exported_data_folder": "dummy_value",
        "files": {
            "whole_slide_imaging_file": image_1,
            "roi_annotations": text,
            "output_summary": csv_1,
            "regions_of_interest": [
                {
                    "binary_seg_map": csv_1,
                    "cell_seg_data": csv_1,
                    "cell_seg_data_summary": csv_1,
                    "phenotype_map": image_1,
                    "region_seg_map": image_1,
                    "score_data": csv_1,
                    "composite_image": image_1,
                    "component_data": image_1,
                }
            ],
        },
    }

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("mif")
    validator.validate(obj)

    # assert negative behaviors
    del obj["records"][0]["project_inform_folder"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)


def test_micsss():

    # create the micsss object
    image = {"slide_scanner_model": "Vectra 2.0", "protocol_name": "E4412"}

    imaging_data = {"internal_slide_id": "a1s1e1"}
    obj = {**ASSAY_CORE, **image, **imaging_data}  # merge three dictionaries

    # create the artifact object
    image_1 = ARTIFACT_OBJ.copy()
    image_1["data_format"] = "IMAGE"
    image_1["height"] = 300
    image_1["width"] = 250
    image_1["channels"] = 3
    csv_1 = ARTIFACT_OBJ.copy()
    csv_1["data_format"] = "CSV"
    csv_1["separator"] = ","
    csv_1["header_row"] = 128
    record = {
        "project_qupath_folder": "dummy",
        "micsss_exported_data_folder": "dummy_value",
        "files": {
            "micsss_output_summary": csv_1,
            "Mapping Artifacts": [
                {
                    "binary_seg_map": csv_1,
                    "cell_seg_data": csv_1,
                    "cell_seg_data_summary": csv_1,
                    "phenotype_map": image_1,
                    "region_seg_map": image_1,
                    "score_data": csv_1,
                }
            ],
            "Composite Image Artifacts": [
                {"composite_image": image_1, "component_data": image_1}
            ],
        },
    }

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("micsss")
    validator.validate(obj)

    # assert negative behaviors
    del obj["records"][0]["project_qupath_folder"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)


def test_olink():

    # create the olink object
    obj = {**ASSAY_CORE}
    obj["panel"] = "panel v1"

    # create the artifact object
    npx = ARTIFACT_OBJ.copy()
    npx["data_format"] = "NPX"
    npx["samples"] = ["CTTTPPPS1.00", "CTTTPPPS2.00", "CTTTPPPS3.00"]
    npx["number_of_samples"] = 3
    csv = ARTIFACT_OBJ.copy()
    csv["data_format"] = "CSV"
    record = OLINK_RECORD.copy()
    record["files"]["assay_npx"] = npx
    record["files"]["assay_raw_ct"] = csv
    record["files"]["study_npx"] = npx

    # add a demo record.
    obj["records"] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("olink")
    validator.validate(obj)

    # assert negative behaviors
    del obj["records"][0]["number_of_samples"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)
