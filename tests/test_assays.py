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
    "md5_hash": "dummy",
    "uploaded_timestamp": "dummy",
    "uploader": "dummy",
    "uuid": "dummy",
    "visible": True
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
        "files": {
            "assay_npx": "",
            "assay_raw_ct": "",
            "study_npx": ""
        }
    }

ASSAY_CORE = {
    "assay_creator": "DFCI",
    "uploader": "dummy",
}


def _fetch_validator(name):

    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "assays/%s_assay.json" % name)
    schema = load_and_validate_schema(schema_path, schema_root)

    # create validator assert schemas are valid.
    return jsonschema.Draft7Validator(schema)


def test_wes():

    # create the ngs object
    ngs_obj = {
        "sequencer_platform": "Illumina - NovaSeq 6000",
        "library_vendor_kit": "KAPA - Hyper Prep",
        "paired_end_reads": "Paired",
        "read_length": 200,
        "input_ng": 666,
        "library_yield_ng": 666,
        "average_insert_size": 200
    }
    obj = {**ASSAY_CORE, **ngs_obj}    # merge two dictionaries

    # create the wes object
    r1 = ARTIFACT_OBJ.copy()
    r1['data_format'] = 'FASTQ'
    rgmf = ARTIFACT_OBJ.copy()
    rgmf['data_format'] = 'TEXT'
    bam = ARTIFACT_OBJ.copy()
    bam['data_format']= 'BAM'
    vcf = ARTIFACT_OBJ.copy()
    vcf['data_format'] = 'VCF'
    rgmf['artifact_category'] = 'Assay Artifact from CIMAC'
    record = {
        "enrichment_vendor_kit": "Twist",
        "enrichment_vendor_lot": "dummy_value",
        "library_kit_lot": "dummy_value",
        "library_prep_date": "01/01/2001",
        "capture_date": "01/01/2001",
        "cimac_id": "CM-TEST-PART-SA",
        "files": {
            "r1": r1,
            "r2": r1,
            "read_group_mapping_file": rgmf
        }
    }

    analysis = {
        "wes_experiment_id": "101010",
        "capture_date": "01/02/2001"          
    }

    # add a demo record.
    obj['records'] = [
        record
    ]

    obj['analysis'] = [
        analysis
    ]

    # create validator assert schemas are valid.
    validator = _fetch_validator("wes")
    validator.validate(obj)

    # assert negative behaviors
    del obj['records'][0]['enrichment_vendor_lot']
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)
    
    # assert negative behaviors for analysis
    del obj['analysis'][0]['wes_experiment_id']
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)


def test_rna_expression():

    # create the ngs object
    ngs_obj = {
        "sequencer_platform": "Illumina - NovaSeq 6000",
        "library_vendor_kit": "KAPA - Hyper Prep",
        "paired_end_reads": "Paired",
        "read_length": 200,
        "input_ng": 666,
        "library_yield_ng": 666,
        "average_insert_size": 200
    }
    obj = {**ASSAY_CORE, **ngs_obj}    # merge two dictionaries

    # add custom entry
    obj['enrichment_method'] = "Ribo minus"

    # create the wes object
    r1 = ARTIFACT_OBJ.copy()
    r1['data_format'] = 'FASTQ'
    rgmf = ARTIFACT_OBJ.copy()
    rgmf['data_format'] = 'TEXT'
    rgmf['artifact_category'] = 'Assay Artifact from CIMAC'
    record = {
        "enrichment_vendor_kit": "Twist",
        "enrichment_vendor_lot": "dummy_value",
        "library_kit_lot": "dummy_value",
        "library_prep_date": "01/01/2001",
        "capture_date": "01/01/2001",
        "cimac_id": "CM-TEST-PART-SA",
        "files": {
            "r1": r1,
            "r2": r1,
            "read_group_mapping_file": rgmf
        }
    }

    # add a demo record.
    obj['records'] = [
        record
    ]

    # create validator assert schemas are valid.
    validator = _fetch_validator("rna_expression")
    validator.validate(obj)

    # assert negative behaviors
    del obj['records'][0]['enrichment_vendor_kit']
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)


def test_cytof():

    # test artifact sub schema
    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "assays/components/cytof/cytof_input.json")
    schema = load_and_validate_schema(schema_path, schema_root)
    validator = jsonschema.Draft7Validator(schema)

    fcs_1 = ARTIFACT_OBJ.copy()
    fcs_1['data_format'] = 'BINARY'
    fcs_2 = ARTIFACT_OBJ.copy()
    fcs_2['data_format'] = 'BINARY'
    record = {
        "processed_fcs": fcs_1,
        "source_fcs": [fcs_2.copy(), fcs_2.copy()]
    }
    validator.validate(record)

    # create the cytof object
    cytof_platform = {
        "instrument": "dummy"
    }

    # create a cytof antibody object.
    antibodies = [
        {
            "antibody": "CD8",
            "isotope": "dummy",
            "dilution": "dummy",
            "stain_type": "Intracellular",
            "usage": "Analysis Only"
        },
        {
            "antibody": "PD-L1",
            "isotope": "dummy",
            "dilution": "dummy",
            "stain_type": "Intracellular",
            "usage": "Used"
        }
    ]
    cytof_panel = {
        "panel_name": "DFCI default",
        "cytof_antibodies": antibodies
    }

    obj = {**ASSAY_CORE, **cytof_platform, **cytof_panel}    # merge three dictionaries

    # create the cytof object
    fcs_1 = ARTIFACT_OBJ.copy()
    fcs_1['data_format'] = 'BINARY'
    fcs_2 = ARTIFACT_OBJ.copy()
    fcs_2['data_format'] = 'BINARY'
    record = {
        "cimac_id": "CM-TEST-PART-SA",
        "files": {
                "processed_fcs": fcs_1,
                "source_fcs": [fcs_2.copy(), fcs_2.copy()]
            }
    }

    # add a demo record.
    obj['records'] = [
        record
    ]

    # create validator assert schemas are valid.
    validator = _fetch_validator("cytof")
    validator.validate(obj)


def test_ihc():

    schema_root = SCHEMA_DIR
    schema_path = os.path.join(SCHEMA_DIR, "assays/components/imaging/ihc_input.json")
    schema = load_and_validate_schema(schema_path, schema_root)
    validator = jsonschema.Draft7Validator(schema)

    # create the IHC object
    ihc_obj = {
        "slide_scanner_model": "Hamamatsu",
        "protocol_name": "E4412",
        "staining_platform": "auto",
    }
    # create the IHC antibody
    antibodies = [
        {
            "antibody": "PD-L1",
            "company": "dummy",
            "clone": "dummy",
            "cat_num": "13684",
            "lot_num": "547645",
            "dilution": "1:200",
            "incubation_time": "1 hr",
            "incubation_temp": "RT"
        },
        {
            "antibody": "PD-L2",
            "company": "dummy",
            "clone": "dummy",
            "cat_num": "13684",
            "lot_num": "547645",
            "dilution": "1:200",
            "incubation_time": "1 hr",
            "incubation_temp": "RT"
        }
    ]

    ihc_a = {
        "antibodies": antibodies
    }
    obj = {**ASSAY_CORE, **ihc_obj, **ihc_a}  # merge three dictionaries

    # create the artifact object
    image_1 = ARTIFACT_OBJ.copy()
    image_1['data_format'] = 'IMAGE'
    image_1["height"] = 300
    image_1["width"] = 250
    image_1["channels"] = 3
    image_2 = ARTIFACT_OBJ.copy()
    image_2['data_format'] = 'IMAGE'
    image_2["height"] = 300
    image_2["width"] = 250
    image_2["channels"] = 3
    csv_1 = ARTIFACT_OBJ.copy()
    csv_1['data_format'] = 'CSV'
    csv_1["separator"] = ","
    csv_1["header_row"] = 128
    record = {
        "percentage_tumor_positive": 80,
        "tumor_positive_intensity": 1,
        "average_tumor_marker_intensity": 1.5,
        "percent_inflammation_marker_positive": 80,
        "average_inflammation_marker_intensity": 1.5,
        "clinically_positive": 1,
        "percentage_viable_tissue": 80,
        "percentage_tumor": 80,
        "degree_lymphoid_infiltrate": 1,
        "percentage_fibrosis": 80,
        "files": {
            "ihc_output_summary": csv_1,
            "ihc_image": image_1,
            "he_image": image_2,
        }
    }

    # add a demo record.
    obj['records'] = [record]

    # create validator assert schemas are valid.
    validator = _fetch_validator("ihc")
    validator.validate(obj)


def test_mif():

    # create the mif object
    image = {
        "slide_scanner_model": "Vectra 2.0",
        "protocol_name": "E4412"
    }

    imaging_data = {
        "internal_slide_id": "a1s1e1"
    }
    obj = {**ASSAY_CORE, **image, **imaging_data}    # merge three dictionaries

    # create the artifact object
    image_1 = ARTIFACT_OBJ.copy()
    image_1['data_format'] = 'IMAGE'
    image_1["height"] = 300
    image_1["width"] = 250
    image_1["channels"] = 3
    csv_1 = ARTIFACT_OBJ.copy()
    csv_1['data_format'] = 'CSV'
    csv_1["separator"] = ","
    csv_1["header_row"] = 128
    text = ARTIFACT_OBJ.copy()
    text['data_format'] = 'TEXT'
    record = {
        "project_inform_folder": "dummy",
        "mif_exported_data_folder": "dummy_value",
        "files":
            {
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
                        "component_data": image_1
                    }]
            }
    }

    # add a demo record.
    obj['records'] = [
        record
    ]

    # create validator assert schemas are valid.
    validator = _fetch_validator("mif")
    validator.validate(obj)

    # assert negative behaviors
    del obj['records'][0]['project_inform_folder']
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)


def test_micsss():

    # create the micsss object
    image = {
        "slide_scanner_model": "Vectra 2.0",
        "protocol_name": "E4412"
    }

    imaging_data = {
        "internal_slide_id": "a1s1e1"
    }
    obj = {**ASSAY_CORE, **image, **imaging_data}    # merge three dictionaries

    # create the artifact object
    image_1 = ARTIFACT_OBJ.copy()
    image_1['data_format'] = 'IMAGE'
    image_1["height"] = 300
    image_1["width"] = 250
    image_1["channels"] = 3
    csv_1 = ARTIFACT_OBJ.copy()
    csv_1['data_format'] = 'CSV'
    csv_1["separator"] = ","
    csv_1["header_row"] = 128
    record = {
        "project_qupath_folder": "dummy",
        "micsss_exported_data_folder": "dummy_value",
        "files":
            {
                "micsss_output_summary": csv_1,
                "Mapping Artifacts": [
                    {
                        "binary_seg_map": csv_1,
                        "cell_seg_data": csv_1,
                        "cell_seg_data_summary": csv_1,
                        "phenotype_map": image_1,
                        "region_seg_map": image_1,
                        "score_data": csv_1,
                    }],
                "Composite Image Artifacts": [
                    {
                        "composite_image": image_1,
                        "component_data": image_1
                    }]
            }
    }

    # add a demo record.
    obj['records'] = [
        record
    ]

    # create validator assert schemas are valid.
    validator = _fetch_validator("micsss")
    validator.validate(obj)

    # assert negative behaviors
    del obj['records'][0]['project_qupath_folder']
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)


def test_olink():

    # create the olink object
    obj = {**ASSAY_CORE}
    obj['panel'] = "panel v1"

    # create the artifact object
    npx = ARTIFACT_OBJ.copy()
    npx['data_format'] = 'NPX'
    npx['samples'] = ['CM-TEST-PART-S1', 'CM-TEST-PART-S2', 'CM-TEST-PART-S3']
    npx['number_of_samples'] = 3
    xlsx = ARTIFACT_OBJ.copy()
    xlsx['data_format'] = 'XLSX'
    record = OLINK_RECORD.copy()
    record["files"]["assay_npx"] = npx
    record["files"]["assay_raw_ct"] = xlsx
    record["files"]["study_npx"] = npx

    # add a demo record.
    obj['records'] = [
        record
    ]

    # create validator assert schemas are valid.
    validator = _fetch_validator("olink")
    validator.validate(obj)

    # assert negative behaviors
    del obj['records'][0]['number_of_samples']
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(obj)
