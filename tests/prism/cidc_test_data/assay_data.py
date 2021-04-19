from cidc_schemas.prism import SUPPORTED_ASSAYS, PROTOCOL_ID_FIELD_NAME

from .utils import (
    copy_dict_with_branch,
    get_prismify_args,
    get_test_trial,
    LocalFileUploadEntry,
    PrismTestData,
)


assay_data_generators = []


def assay_data_generator(f):
    assay_data_generators.append(f)
    return f


@assay_data_generator
def clinical_data() -> PrismTestData:
    upload_type = "clinical_data"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "clinical_data": {
            "assay_creator": "DFCI",
            "records": [
                {
                    "clinical_file": {
                        "upload_placeholder": "28ec20a1-d2dc-46aa-91be-819b684da268"
                    },
                    "comment": "no comment",
                }
            ],
        },
        "protocol_identifier": "test_prism_trial_id",
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="test_file.xlsx",
            gs_key="test_prism_trial_id/clinical/response.xlsx",
            upload_placeholder="28ec20a1-d2dc-46aa-91be-819b684da268",
            metadata_availability=True,
            allow_empty=False,
        )
    ]

    base_trial = get_test_trial([])

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "clinical_data")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def cytof_10021() -> PrismTestData:
    upload_type = "cytof_10021"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "assays": {
            "cytof_10021": [
                {
                    "records": [
                        {
                            "cimac_id": "CTTTPP111.00",
                            "input_files": {
                                "intermediate_fcs": {
                                    "upload_placeholder": "28ec20a1-d2dc-46aa-91be-819b684da268"
                                },
                                "processed_fcs": {
                                    "upload_placeholder": "97c3b6a6-b03d-4ca1-92f8-b8651e51d0c6"
                                },
                            },
                            "concatenation_version": "GHIL",
                            "normalization_version": "ABC",
                            "debarcoding_key": "FLUIDIGM 1234",
                            "preprocessing_notes": "a note like any other note",
                        },
                        {
                            "cimac_id": "CTTTPP121.00",
                            "input_files": {
                                "intermediate_fcs": {
                                    "upload_placeholder": "8a674ce1-e224-45b7-8094-77fca9f98ae2"
                                },
                                "processed_fcs": {
                                    "upload_placeholder": "7e992a16-9c6a-4ef1-90b8-ef1a599b88bc"
                                },
                            },
                            "concatenation_version": "GHIL",
                            "normalization_version": "ABC",
                            "debarcoding_key": "FLUIDIGM 1234",
                            "preprocessing_notes": "a different note",
                        },
                    ],
                    "assay_run_id": "test_prism_trial_id_run_1",
                    "assay_creator": "DFCI",
                    "instrument": "PresNixon123",
                    "source_fcs": [
                        {"upload_placeholder": "4918a014-0e63-4a36-a45a-c62d593e225e"},
                        {"upload_placeholder": "0bbd7520-18b9-4ec3-8344-49f02dcadb08"},
                    ],
                    "batch_id": "XYZ1",
                    "injector": "HAT123",
                    "date_of_acquisition": "43355",
                    "acquisition_buffer": "ABC",
                    "bead_removal": True,
                    "normalization_method": "Fluidigm",
                    "debarcoding_protocol": "Fluidigm",
                    "harware_version": "Fluidigm 3.0.2",
                    "cytof_antibodies": [
                        {
                            "antibody": "CD8",
                            "clone": "C8/144b",
                            "company": "DAKO",
                            "cat_num": "C8-ABC",
                            "lot_num": "3983272",
                            "isotope": "146Nd",
                            "dilution": "100X",
                            "stain_type": "Surface Stain",
                            "usage": "Used",
                        },
                        {
                            "antibody": "PD-L1",
                            "clone": "C2/11p",
                            "company": "DAKO",
                            "cat_num": "C8-AB123",
                            "lot_num": "1231272",
                            "isotope": "146Nb",
                            "dilution": "100X",
                            "stain_type": "Surface Stain",
                            "usage": "Analysis Only",
                        },
                    ],
                }
            ]
        },
        "protocol_identifier": "test_prism_trial_id",
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="sample1_n.fcs",
            gs_key="test_prism_trial_id/cytof_10021/CTTTPP111.00/intermediate.fcs",
            upload_placeholder="28ec20a1-d2dc-46aa-91be-819b684da268",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="sample1.fcs",
            gs_key="test_prism_trial_id/cytof_10021/CTTTPP111.00/processed.fcs",
            upload_placeholder="97c3b6a6-b03d-4ca1-92f8-b8651e51d0c6",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="sample2_n.fcs",
            gs_key="test_prism_trial_id/cytof_10021/CTTTPP121.00/intermediate.fcs",
            upload_placeholder="8a674ce1-e224-45b7-8094-77fca9f98ae2",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="sample2.fcs",
            gs_key="test_prism_trial_id/cytof_10021/CTTTPP121.00/processed.fcs",
            upload_placeholder="7e992a16-9c6a-4ef1-90b8-ef1a599b88bc",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="batch1f1.fcs",
            gs_key="test_prism_trial_id/cytof_10021/XYZ1/source_0.fcs",
            upload_placeholder="4918a014-0e63-4a36-a45a-c62d593e225e",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="batch1f2.fcs",
            gs_key="test_prism_trial_id/cytof_10021/XYZ1/source_1.fcs",
            upload_placeholder="0bbd7520-18b9-4ec3-8344-49f02dcadb08",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["cytof_10021"]
        for record in batch["records"]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def cytof_e4412() -> PrismTestData:
    upload_type = "cytof_e4412"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "assays": {
            "cytof_e4412": [
                {
                    "participants": [
                        {
                            "cimac_participant_id": "CTTTPP1",
                            "participant_debarcoding_key": "FOOBAR",
                            "preprocessing_notes": "testing a participant note",
                            "control": {
                                "input_files": {
                                    "processed_fcs": {
                                        "upload_placeholder": "28ec20a1-d2dc-46aa-91be-819b684da268"
                                    }
                                },
                                "concatenation_version": "GHIL",
                                "normalization_version": "ABC",
                                "debarcoding_key": "FLUIDIGM 1234",
                                "preprocessing_notes": "a note like any other note",
                            },
                            "samples": [
                                {
                                    "cimac_id": "CTTTPP111.00",
                                    "input_files": {
                                        "processed_fcs": {
                                            "upload_placeholder": "97c3b6a6-b03d-4ca1-92f8-b8651e51d0c6"
                                        }
                                    },
                                    "concatenation_version": "GHIL",
                                    "normalization_version": "ABC",
                                    "debarcoding_key": "FLUIDIGM 1234",
                                    "preprocessing_notes": "a note like any other note",
                                },
                                {
                                    "cimac_id": "CTTTPP121.00",
                                    "input_files": {
                                        "processed_fcs": {
                                            "upload_placeholder": "7e992a16-9c6a-4ef1-90b8-ef1a599b88bc"
                                        }
                                    },
                                    "concatenation_version": "GHIL",
                                    "normalization_version": "ABC",
                                    "debarcoding_key": "FLUIDIGM 1234",
                                    "preprocessing_notes": "a different note",
                                },
                            ],
                        },
                        {
                            "cimac_participant_id": "CTTTPP2",
                            "participant_debarcoding_key": "BIZBUZ",
                            "control": {
                                "input_files": {
                                    "processed_fcs": {
                                        "upload_placeholder": "8a674ce1-e224-45b7-8094-77fca9f98ae2"
                                    }
                                },
                                "concatenation_version": "GHIL",
                                "normalization_version": "ABC",
                                "debarcoding_key": "FLUIDIGM 1234",
                                "preprocessing_notes": "a different note",
                            },
                            "samples": [
                                {
                                    "cimac_id": "CTTTPP211.00",
                                    "input_files": {
                                        "processed_fcs": {
                                            "upload_placeholder": "0bbd7520-18b9-4ec3-8344-49f02dcadb08"
                                        }
                                    },
                                    "concatenation_version": "GHIL",
                                    "normalization_version": "ABC",
                                    "debarcoding_key": "FLUIDIGM 1234",
                                    "preprocessing_notes": "a note like any other note",
                                }
                            ],
                        },
                    ],
                    "assay_run_id": "test_prism_trial_id_run_1",
                    "assay_creator": "DFCI",
                    "source_fcs": [
                        {"upload_placeholder": "4918a014-0e63-4a36-a45a-c62d593e225e"}
                    ],
                    "batch_id": "XYZ1",
                    "acquisition_buffer": "ABC",
                    "debarcoding_protocol": "Fluidigm",
                    "cytof_antibodies": [
                        {
                            "antibody": "CD8",
                            "clone": "C8/144b",
                            "company": "DAKO",
                            "cat_num": "C8-ABC",
                            "lot_num": "3983272",
                            "isotope": "146Nd",
                            "dilution": "100X",
                            "stain_type": "Surface Stain",
                            "usage": "Used",
                        },
                        {
                            "antibody": "PD-L1",
                            "clone": "C2/11p",
                            "company": "DAKO",
                            "cat_num": "C8-AB123",
                            "lot_num": "1231272",
                            "isotope": "146Nb",
                            "dilution": "100X",
                            "stain_type": "Surface Stain",
                            "usage": "Analysis Only",
                        },
                    ],
                }
            ]
        },
        "protocol_identifier": "test_prism_trial_id",
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="control1.fcs",
            gs_key="test_prism_trial_id/cytof_e4412/CTTTPP1_control/processed.fcs",
            upload_placeholder="28ec20a1-d2dc-46aa-91be-819b684da268",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="sample1.fcs",
            gs_key="test_prism_trial_id/cytof_e4412/CTTTPP111.00/processed.fcs",
            upload_placeholder="97c3b6a6-b03d-4ca1-92f8-b8651e51d0c6",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="sample2.fcs",
            gs_key="test_prism_trial_id/cytof_e4412/CTTTPP121.00/processed.fcs",
            upload_placeholder="7e992a16-9c6a-4ef1-90b8-ef1a599b88bc",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="control2.fcs",
            gs_key="test_prism_trial_id/cytof_e4412/CTTTPP2_control/processed.fcs",
            upload_placeholder="8a674ce1-e224-45b7-8094-77fca9f98ae2",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="sample3.fcs",
            gs_key="test_prism_trial_id/cytof_e4412/CTTTPP211.00/processed.fcs",
            upload_placeholder="0bbd7520-18b9-4ec3-8344-49f02dcadb08",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="batch1f1.fcs",
            gs_key="test_prism_trial_id/cytof_e4412/XYZ1/source_0.fcs",
            upload_placeholder="4918a014-0e63-4a36-a45a-c62d593e225e",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["cytof_e4412"]
        for participant in batch["participants"]
        for record in participant["samples"]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def ihc() -> PrismTestData:
    upload_type = "ihc"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "123",  # testing integer protocol id
        "assays": {
            "ihc": [
                {
                    "records": [
                        {
                            "cimac_id": "CTTTPP111.00",
                            "files": {
                                "ihc_image": {
                                    "upload_placeholder": "e4294fb9-047f-4df6-b614-871289a1a2a8"
                                }
                            },
                            "marker_positive": "positive",
                            "tumor_proportion_score": 0.67,
                            "intensity": 0.0,
                            "percentage_expression": 0.0,
                            "h_score": 0,
                        },
                        {
                            "cimac_id": "CTTTPP121.00",
                            "files": {
                                "ihc_image": {
                                    "upload_placeholder": "fba3f94b-669c-48c7-aee0-f0d5e5e8a341"
                                }
                            },
                            "marker_positive": "no_call",
                            "tumor_proportion_score": 0.1,
                            "intensity": 1.0,
                            "percentage_expression": 10.0,
                            "h_score": 120,
                        },
                        {
                            "cimac_id": "CTTTPP122.00",
                            "files": {
                                "ihc_image": {
                                    "upload_placeholder": "ecd3f6ea-8315-4fa9-bb37-501b4e821aed"
                                }
                            },
                            "marker_positive": "negative",
                            "tumor_proportion_score": 0.1,
                            "intensity": 2.0,
                            "percentage_expression": 40.0,
                            "h_score": 299,
                        },
                        {
                            "cimac_id": "CTTTPP123.00",
                            "files": {
                                "ihc_image": {
                                    "upload_placeholder": "af19deb2-a66e-4c2c-960c-308781245c69"
                                }
                            },
                            "marker_positive": "positive",
                            "tumor_proportion_score": 0.2,
                            "intensity": 3.0,
                            "percentage_expression": 100.0,
                            "h_score": 300,
                        },
                    ],
                    "assay_creator": "DFCI",
                    "slide_scanner_model": "Vectra 2.0",
                    "staining_platform": "auto",
                    "autostainer_model": "Bond RX",
                    "antibody": {
                        "antibody": "XYZ",
                        "company": "XYZ",
                        "clone": "XYZ",
                        "cat_num": "ABX.123",
                        "lot_num": "#12345",
                        "dilution": "1900-01-04 04:05:00",
                        "incubation_time": "06:45:00",
                        "incubation_temp": "54c",
                    },
                }
            ]
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="path/to/image1.tif",
            gs_key="123/ihc/CTTTPP111.00/ihc_image.tif",
            upload_placeholder="e4294fb9-047f-4df6-b614-871289a1a2a8",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="path/to/image2.tiff",
            gs_key="123/ihc/CTTTPP121.00/ihc_image.tiff",
            upload_placeholder="fba3f94b-669c-48c7-aee0-f0d5e5e8a341",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="path/to/image3.svs",
            gs_key="123/ihc/CTTTPP122.00/ihc_image.svs",
            upload_placeholder="ecd3f6ea-8315-4fa9-bb37-501b4e821aed",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="path/to/image4.qptiff",
            gs_key="123/ihc/CTTTPP123.00/ihc_image.qptiff",
            upload_placeholder="af19deb2-a66e-4c2c-960c-308781245c69",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["ihc"]
        for record in batch["records"]
    ]
    base_trial = get_test_trial(cimac_ids)

    base_trial[PROTOCOL_ID_FIELD_NAME] = "123"

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def hande() -> PrismTestData:
    upload_type = "hande"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "123",
        "assays": {
            "hande": [
                {
                    "records": [
                        {
                            "cimac_id": "CTTTPP111.00",
                            "files": {
                                "image_file": {
                                    "upload_placeholder": "eeeeeeee-047f-4df6-b614-871289a1a2a8"
                                }
                            },
                            "comment": "a comment",
                        },
                        {
                            "cimac_id": "CTTTPP121.00",
                            "files": {
                                "image_file": {
                                    "upload_placeholder": "eeeeeeee-669c-48c7-aee0-f0d5e5e8a341"
                                }
                            },
                            "comment": "another comment",
                        },
                    ],
                    "assay_creator": "DFCI",
                }
            ]
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="path/to/image1.svs",
            gs_key="123/hande/CTTTPP111.00/image_file.svs",
            upload_placeholder="eeeeeeee-047f-4df6-b614-871289a1a2a8",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="path/to/image2.svs",
            gs_key="123/hande/CTTTPP121.00/image_file.svs",
            upload_placeholder="eeeeeeee-669c-48c7-aee0-f0d5e5e8a341",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["hande"]
        for record in batch["records"]
    ]
    base_trial = get_test_trial(cimac_ids)

    base_trial[PROTOCOL_ID_FIELD_NAME] = "123"

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def wes_bam() -> PrismTestData:
    upload_type = "wes_bam"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "wes": [
                {
                    "records": [
                        {
                            "cimac_id": "CTTTPP111.00",
                            "files": {
                                "bam": [
                                    {
                                        "upload_placeholder": "d75a0a45-50dd-4aa5-bd46-2793bd5c84e5"
                                    },
                                    {
                                        "upload_placeholder": "3385fc87-9630-440b-9924-448168050170"
                                    },
                                ]
                            },
                            "sequencing_date": "2010-01-01 00:00:00",
                            "quality_flag": 1.0,
                        },
                        {
                            "cimac_id": "CTTTPP121.00",
                            "files": {
                                "bam": [
                                    {
                                        "upload_placeholder": "c2ffea21-0771-45ca-bd08-f384b012afb9"
                                    },
                                    {
                                        "upload_placeholder": "b5952706-527d-4a6c-b085-97cb02059da6"
                                    },
                                ]
                            },
                            "sequencing_date": "2010-01-01 00:00:00",
                            "quality_flag": 1.0,
                        },
                    ],
                    "assay_creator": "Mount Sinai",
                    "sequencing_protocol": "Express Somatic Human WES (Deep Coverage) v1.1",
                    "library_kit": "Hyper Prep ICE Exome Express: 1.0",
                    "sequencer_platform": "Illumina - NextSeq 550",
                    "paired_end_reads": "Paired",
                    "read_length": 100,
                    "bait_set": "whole_exome_illumina_coding_v1",
                }
            ]
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="gs://local/path/to/fwd.1.1.1.bam",
            gs_key="test_prism_trial_id/wes/CTTTPP111.00/reads_0.bam",
            upload_placeholder="d75a0a45-50dd-4aa5-bd46-2793bd5c84e5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://local/path/to/fwd.1.1.1_2.bam",
            gs_key="test_prism_trial_id/wes/CTTTPP111.00/reads_1.bam",
            upload_placeholder="3385fc87-9630-440b-9924-448168050170",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://local/path/to/fwd.1.2.1.bam",
            gs_key="test_prism_trial_id/wes/CTTTPP121.00/reads_0.bam",
            upload_placeholder="c2ffea21-0771-45ca-bd08-f384b012afb9",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://local/path/to/fwd.1.2.1_2.bam",
            gs_key="test_prism_trial_id/wes/CTTTPP121.00/reads_1.bam",
            upload_placeholder="b5952706-527d-4a6c-b085-97cb02059da6",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["wes"]
        for record in batch["records"]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def wes_fastq() -> PrismTestData:
    upload_type = "wes_fastq"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "wes": [
                {
                    "records": [
                        {
                            "cimac_id": "CTTTPP111.00",
                            "files": {
                                "r1": [
                                    {
                                        "upload_placeholder": "3c8b4fe4-780a-4431-908f-aa879c01c009"
                                    },
                                    {
                                        "upload_placeholder": "c665c9ca-7065-46b8-b1c8-b871e15db294"
                                    },
                                ],
                                "r2": [
                                    {
                                        "upload_placeholder": "82bc1123-55e2-4640-a9c9-a259d5756a86"
                                    }
                                ],
                            },
                            "sequencing_date": "2010-01-01 00:00:00",
                            "quality_flag": 1.0,
                        },
                        {
                            "cimac_id": "CTTTPP121.00",
                            "files": {
                                "r1": [
                                    {
                                        "upload_placeholder": "4d57fa58-5dd4-4379-878d-935d79d2507f"
                                    },
                                    {
                                        "upload_placeholder": "c24a1b3d-a19a-414a-9fc4-55bcbb7db9ec"
                                    },
                                ],
                                "r2": [
                                    {
                                        "upload_placeholder": "5eb4b639-c2a4-48f8-85f8-e9a04f5233c6"
                                    }
                                ],
                            },
                            "sequencing_date": "2010-01-01 00:00:00",
                            "quality_flag": 1.0,
                        },
                    ],
                    "assay_creator": "Mount Sinai",
                    "sequencing_protocol": "Express Somatic Human WES (Deep Coverage) v1.1",
                    "library_kit": "Hyper Prep ICE Exome Express: 1.0",
                    "sequencer_platform": "Illumina - NextSeq 550",
                    "paired_end_reads": "Paired",
                    "read_length": 100,
                    "bait_set": "whole_exome_illumina_coding_v1",
                }
            ]
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="/local/path/to/fwd.1.1.1.fastq.gz",
            gs_key="test_prism_trial_id/wes/CTTTPP111.00/r1_0.fastq.gz",
            upload_placeholder="3c8b4fe4-780a-4431-908f-aa879c01c009",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/fwd.1.1.1_2.fastq.gz",
            gs_key="test_prism_trial_id/wes/CTTTPP111.00/r1_1.fastq.gz",
            upload_placeholder="c665c9ca-7065-46b8-b1c8-b871e15db294",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/rev.1.1.1.fastq.gz",
            gs_key="test_prism_trial_id/wes/CTTTPP111.00/r2_0.fastq.gz",
            upload_placeholder="82bc1123-55e2-4640-a9c9-a259d5756a86",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/fwd.1.2.1.fastq.gz",
            gs_key="test_prism_trial_id/wes/CTTTPP121.00/r1_0.fastq.gz",
            upload_placeholder="4d57fa58-5dd4-4379-878d-935d79d2507f",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/fwd.1.2.1_2.fastq.gz",
            gs_key="test_prism_trial_id/wes/CTTTPP121.00/r1_1.fastq.gz",
            upload_placeholder="c24a1b3d-a19a-414a-9fc4-55bcbb7db9ec",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/rev.1.2.1.fastq.gz",
            gs_key="test_prism_trial_id/wes/CTTTPP121.00/r2_0.fastq.gz",
            upload_placeholder="5eb4b639-c2a4-48f8-85f8-e9a04f5233c6",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["wes"]
        for record in batch["records"]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def rna_bam() -> PrismTestData:
    upload_type = "rna_bam"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "rna": [
                {
                    "records": [
                        {
                            "cimac_id": "CTTTPP122.00",
                            "files": {
                                "bam": [
                                    {
                                        "upload_placeholder": "8c85011c-ccee-49b4-a940-be6ece437953"
                                    },
                                    {
                                        "upload_placeholder": "5cebf955-8f5b-4523-807b-3bd3cf5811f6"
                                    },
                                ]
                            },
                            "library_yield_ng": 600.0,
                            "dv200": 0.7,
                            "rqs": 8.0,
                            "quality_flag": 1.0,
                        },
                        {
                            "cimac_id": "CTTTPP123.00",
                            "files": {
                                "bam": [
                                    {
                                        "upload_placeholder": "10859cc5-8258-4d00-9118-9939b354a519"
                                    },
                                    {
                                        "upload_placeholder": "c7cf5b84-b924-48dd-9f7b-a32efd6a7b0d"
                                    },
                                ]
                            },
                            "dv200": 0.8,
                            "rqs": 9.0,
                            "rin": 9.0,
                            "quality_flag": 1.0,
                        },
                    ],
                    "assay_creator": "DFCI",
                    "enrichment_method": "Transcriptome capture v1",
                    "sequencer_platform": "Illumina - HiSeq 3000",
                    "paired_end_reads": "Paired",
                }
            ]
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="gs://local/path/to/fwd.1.1.1.bam",
            gs_key="test_prism_trial_id/rna/CTTTPP122.00/reads_0.bam",
            upload_placeholder="8c85011c-ccee-49b4-a940-be6ece437953",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://local/path/to/fwd.1.1.1_2.bam",
            gs_key="test_prism_trial_id/rna/CTTTPP122.00/reads_1.bam",
            upload_placeholder="5cebf955-8f5b-4523-807b-3bd3cf5811f6",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://local/path/to/fwd.1.2.1.bam",
            gs_key="test_prism_trial_id/rna/CTTTPP123.00/reads_0.bam",
            upload_placeholder="10859cc5-8258-4d00-9118-9939b354a519",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://local/path/to/fwd.1.2.1_2.bam",
            gs_key="test_prism_trial_id/rna/CTTTPP123.00/reads_1.bam",
            upload_placeholder="c7cf5b84-b924-48dd-9f7b-a32efd6a7b0d",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["rna"]
        for record in batch["records"]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def rna_fastq() -> PrismTestData:
    upload_type = "rna_fastq"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "rna": [
                {
                    "records": [
                        {
                            "cimac_id": "CTTTPP122.00",
                            "files": {
                                "r1": [
                                    {
                                        "upload_placeholder": "2635df00-082b-4e2d-92a8-7a5e629483db"
                                    },
                                    {
                                        "upload_placeholder": "b0723fe8-5533-40e0-86cb-16162d8683e4"
                                    },
                                ],
                                "r2": [
                                    {
                                        "upload_placeholder": "1cd2bb4f-3f84-4f78-b387-4edb6dcc5d1b"
                                    }
                                ],
                            },
                            "library_yield_ng": 600.0,
                            "dv200": 0.7,
                            "rqs": 8.0,
                            "quality_flag": 1.0,
                        },
                        {
                            "cimac_id": "CTTTPP123.00",
                            "files": {
                                "r1": [
                                    {
                                        "upload_placeholder": "d49521dc-d531-4555-a874-80aa0ce31dc1"
                                    },
                                    {
                                        "upload_placeholder": "5ebfef93-5c4c-496d-b8ae-13c1978322d2"
                                    },
                                ],
                                "r2": [
                                    {
                                        "upload_placeholder": "ae150200-c6b2-459c-a264-b56bc2aca263"
                                    }
                                ],
                            },
                            "library_yield_ng": 650.0,
                            "dv200": 0.8,
                            "rqs": 9.0,
                            "rin": 9.0,
                            "quality_flag": 1.0,
                        },
                    ],
                    "assay_creator": "DFCI",
                    "enrichment_method": "Transcriptome capture v1",
                    "enrichment_vendor_kit": "Illumina - TruSeq Stranded PolyA mRNA",
                    "sequencer_platform": "Illumina - HiSeq 3000",
                    "paired_end_reads": "Paired",
                }
            ]
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="/local/path/to/fwd.1.1.1.fastq.gz",
            gs_key="test_prism_trial_id/rna/CTTTPP122.00/r1_0.fastq.gz",
            upload_placeholder="2635df00-082b-4e2d-92a8-7a5e629483db",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/fwd.1.1.1_2.fastq.gz",
            gs_key="test_prism_trial_id/rna/CTTTPP122.00/r1_1.fastq.gz",
            upload_placeholder="b0723fe8-5533-40e0-86cb-16162d8683e4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/rev.1.1.1.fastq.gz",
            gs_key="test_prism_trial_id/rna/CTTTPP122.00/r2_0.fastq.gz",
            upload_placeholder="1cd2bb4f-3f84-4f78-b387-4edb6dcc5d1b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/fwd.1.2.1.fastq.gz",
            gs_key="test_prism_trial_id/rna/CTTTPP123.00/r1_0.fastq.gz",
            upload_placeholder="d49521dc-d531-4555-a874-80aa0ce31dc1",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/fwd.1.2.1_2.fastq.gz",
            gs_key="test_prism_trial_id/rna/CTTTPP123.00/r1_1.fastq.gz",
            upload_placeholder="5ebfef93-5c4c-496d-b8ae-13c1978322d2",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/rev.1.2.1.fastq.gz",
            gs_key="test_prism_trial_id/rna/CTTTPP123.00/r2_0.fastq.gz",
            upload_placeholder="ae150200-c6b2-459c-a264-b56bc2aca263",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["rna"]
        for record in batch["records"]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def tcr_fastq() -> PrismTestData:
    upload_type = "tcr_fastq"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "tcr": [
                {
                    "records": [
                        {
                            "cimac_id": "CTTTPP111.00",
                            "files": {
                                "replicates": [
                                    {
                                        "replicate_id": "1A",
                                        "r1": [
                                            {
                                                "upload_placeholder": "3635df00-082b-4e2d-92a8-7a5e629483dc"
                                            }
                                        ],
                                        "r2": [
                                            {
                                                "upload_placeholder": "2cd2bb4f-3f84-4f78-b387-4edb6dcc5d1c"
                                            }
                                        ],
                                        "i1": [
                                            {
                                                "upload_placeholder": "aa35df00-082b-4e2d-92a8-7a5e629483dc"
                                            }
                                        ],
                                        "i2": [
                                            {
                                                "upload_placeholder": "bbd2bb4f-3f84-4f78-b387-4edb6dcc5d1c"
                                            }
                                        ],
                                        "rna_quantity_ng": 600.0,
                                    }
                                ]
                            },
                        },
                        {
                            "cimac_id": "CTTTPP121.00",
                            "files": {
                                "replicates": [
                                    {
                                        "replicate_id": "1A",
                                        "r1": [
                                            {
                                                "upload_placeholder": "e49521dc-d531-4555-a874-80aa0ce31dc2"
                                            }
                                        ],
                                        "r2": [
                                            {
                                                "upload_placeholder": "be150200-c6b2-459c-a264-b56bc2aca264"
                                            }
                                        ],
                                        "i1": [
                                            {
                                                "upload_placeholder": "cc9521dc-d531-4555-a874-80aa0ce31dc2"
                                            }
                                        ],
                                        "i2": [
                                            {
                                                "upload_placeholder": "dd150200-c6b2-459c-a264-b56bc2aca264"
                                            }
                                        ],
                                        "rna_quantity_ng": 650.0,
                                    },
                                    {
                                        "replicate_id": "2A",
                                        "r1": [
                                            {
                                                "upload_placeholder": "r29521dc-d531-4555-a874-80aa0ce31dc2"
                                            }
                                        ],
                                        "r2": [
                                            {
                                                "upload_placeholder": "r2150200-c6b2-459c-a264-b56bc2aca264"
                                            }
                                        ],
                                        "i1": [
                                            {
                                                "upload_placeholder": "r29521dc-d531-4555-a874-80aa0ce31dc3"
                                            }
                                        ],
                                        "i2": [
                                            {
                                                "upload_placeholder": "r2150200-c6b2-459c-a264-b56bc2aca265"
                                            }
                                        ],
                                        "rna_quantity_ng": 10.0,
                                    },
                                ]
                            },
                        },
                    ],
                    "assay_creator": "Mount Sinai",
                    "sequencer_platform": "Illumina - HiSeq 3000",
                    "batch_id": "XYZ",
                    "sequencing_run_date": "2019-12-12 00:00:00",
                    "sample_sheet": {
                        "upload_placeholder": "rb150200-c6b2-459c-a264-b56bc2aca26a"
                    },
                }
            ]
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="/local/path/to/read1_1.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP111.00/replicate_1A/r1.fastq.gz",
            upload_placeholder="3635df00-082b-4e2d-92a8-7a5e629483dc",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/read2_1.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP111.00/replicate_1A/r2.fastq.gz",
            upload_placeholder="2cd2bb4f-3f84-4f78-b387-4edb6dcc5d1c",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/index1_1.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP111.00/replicate_1A/i1.fastq.gz",
            upload_placeholder="aa35df00-082b-4e2d-92a8-7a5e629483dc",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/index2_1.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP111.00/replicate_1A/i2.fastq.gz",
            upload_placeholder="bbd2bb4f-3f84-4f78-b387-4edb6dcc5d1c",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/read1_2.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP121.00/replicate_1A/r1.fastq.gz",
            upload_placeholder="e49521dc-d531-4555-a874-80aa0ce31dc2",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/read2_2.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP121.00/replicate_1A/r2.fastq.gz",
            upload_placeholder="be150200-c6b2-459c-a264-b56bc2aca264",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/index1_2.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP121.00/replicate_1A/i1.fastq.gz",
            upload_placeholder="cc9521dc-d531-4555-a874-80aa0ce31dc2",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/index2_2.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP121.00/replicate_1A/i2.fastq.gz",
            upload_placeholder="dd150200-c6b2-459c-a264-b56bc2aca264",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/read1_3.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP121.00/replicate_2A/r1.fastq.gz",
            upload_placeholder="r29521dc-d531-4555-a874-80aa0ce31dc2",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/read2_3.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP121.00/replicate_2A/r2.fastq.gz",
            upload_placeholder="r2150200-c6b2-459c-a264-b56bc2aca264",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/index1_3.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP121.00/replicate_2A/i1.fastq.gz",
            upload_placeholder="r29521dc-d531-4555-a874-80aa0ce31dc3",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/index2_3.fastq.gz",
            gs_key="test_prism_trial_id/tcr/XYZ/CTTTPP121.00/replicate_2A/i2.fastq.gz",
            upload_placeholder="r2150200-c6b2-459c-a264-b56bc2aca265",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="/local/path/to/sample_sheet.csv",
            gs_key="test_prism_trial_id/tcr/XYZ/SampleSheet.csv",
            upload_placeholder="rb150200-c6b2-459c-a264-b56bc2aca26a",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["tcr"]
        for record in batch["records"]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def olink() -> PrismTestData:
    upload_type = "olink"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "olink": {
                "batches": [
                    {
                        "batch_id": "batch1",
                        "records": [
                            {
                                "chip_barcode": "1111",
                                "files": {
                                    "assay_npx": {
                                        "upload_placeholder": "d658b480-ed78-4717-b622-3e84bde632b6"
                                    },
                                    "assay_raw_ct": {
                                        "upload_placeholder": "4e9d0a47-90dc-4134-9ad6-3e3dd83619d6"
                                    },
                                },
                                "run_date": "2019-12-12 00:00:00",
                                "run_time": "10:11:00",
                                "instrument": "MIOMARKHD411",
                                "fludigm_application_version": "4.1.3",
                                "fludigm_application_build": "20140305.43",
                                "probe_type": "FAM-MGB",
                                "passive_reference": "ROX",
                                "quality_threshold": 0.5,
                                "baseline_correction": "Linear",
                                "number_of_samples": 90.0,
                                "number_of_samples_failed": 5.0,
                                "npx_manager_version": "Olink NPX Manager 0.0.82.0",
                            },
                            {
                                "chip_barcode": "1112",
                                "files": {
                                    "assay_npx": {
                                        "upload_placeholder": "9855c579-82e0-42ee-8225-7c1c736bb69f"
                                    },
                                    "assay_raw_ct": {
                                        "upload_placeholder": "b387e41a-1c6a-42b5-aa16-dccf6249e404"
                                    },
                                },
                                "run_date": "2019-12-12 00:00:00",
                                "run_time": "10:11:00",
                                "instrument": "MIOMARKHD411",
                                "fludigm_application_version": "4.1.3",
                                "fludigm_application_build": "20140305.43",
                                "probe_type": "FAM-MGB",
                                "passive_reference": "ROX",
                                "quality_threshold": 0.5,
                                "baseline_correction": "Linear",
                                "number_of_samples": 80.0,
                                "number_of_samples_failed": 10.0,
                                "npx_manager_version": "Olink NPX Manager 0.0.82.0",
                            },
                        ],
                        "assay_creator": "DFCI",
                        "panel": "Olink INFLAMMATION(v.3004)",
                        "assay_panel_lot": "1",
                        "combined": {
                            "npx_file": {
                                "upload_placeholder": "1b0b3b8f-6417-4a37-85dc-e8aa75594678"
                            },
                            "npx_manager_version": "Olink NPX Manager 0.0.82.0",
                        },
                    }
                ],
                "study": {
                    "npx_file": {
                        "upload_placeholder": "19b31c40-a3dd-4be1-b9bd-022b9ff08dfd"
                    },
                    "npx_manager_version": "Olink NPX Manager 0.0.82.0",
                },
            }
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="olink_assay_1_NPX.xlsx",
            gs_key="test_prism_trial_id/olink/batch_batch1/chip_1111/assay_npx.xlsx",
            upload_placeholder="d658b480-ed78-4717-b622-3e84bde632b6",
            metadata_availability=True,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="olink_assay_1_CT.csv",
            gs_key="test_prism_trial_id/olink/batch_batch1/chip_1111/assay_raw_ct.csv",
            upload_placeholder="4e9d0a47-90dc-4134-9ad6-3e3dd83619d6",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="olink_assay_2_NPX.xlsx",
            gs_key="test_prism_trial_id/olink/batch_batch1/chip_1112/assay_npx.xlsx",
            upload_placeholder="9855c579-82e0-42ee-8225-7c1c736bb69f",
            metadata_availability=True,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="olink_assay_2_CT.csv",
            gs_key="test_prism_trial_id/olink/batch_batch1/chip_1112/assay_raw_ct.csv",
            upload_placeholder="b387e41a-1c6a-42b5-aa16-dccf6249e404",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="olink_assay_combined.xlsx",
            gs_key="test_prism_trial_id/olink/study_npx.xlsx",
            upload_placeholder="19b31c40-a3dd-4be1-b9bd-022b9ff08dfd",
            metadata_availability=True,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="olink_assay_batch_combined.xlsx",
            gs_key="test_prism_trial_id/olink/batch_batch1/combined_npx.xlsx",
            upload_placeholder="1b0b3b8f-6417-4a37-85dc-e8aa75594678",
            metadata_availability=True,
            allow_empty=False,
        ),
    ]
    base_trial = get_test_trial()

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def elisa() -> PrismTestData:
    upload_type = "elisa"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "elisa": [
                {
                    "antigens": [
                        {
                            "antigen": "GST",
                            "antigen_type": "protein",
                            "final_concentration": 1.0,
                            "final_concentration_units": "Nanogram per Microliter",
                        },
                        {
                            "antigen": "p53 16-32",
                            "antigen_type": "peptide",
                            "final_concentration": 1.0,
                            "final_concentration_units": "Micromolar",
                        },
                    ],
                    "assay_creator": "DFCI",
                    "assay_run_id": "test_prism_trial_id_run_1",
                    "assay_xlsx": {
                        "upload_placeholder": "69b033d4-c895-4fb4-88e8-9b2a5e264874"
                    },
                }
            ]
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="otest_prism_trial_id_run_1_ELISA.xlsx",
            gs_key="test_prism_trial_id/elisa/test_prism_trial_id_run_1/assay.xlsx",
            upload_placeholder="69b033d4-c895-4fb4-88e8-9b2a5e264874",
            metadata_availability=True,
            allow_empty=False,
        )
    ]
    base_trial = get_test_trial()

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def mif() -> PrismTestData:
    upload_type = "mif"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "mif": [
                {
                    "panel": "Panel 1: PD-L1, CD68, PD-1, CD8, CD3, pan-cytokeratin, DAPI",
                    "antibodies": [
                        {
                            "antibody": "CD8",
                            "export_name": "CD8 (Opal 540)",
                            "clone": "C8/144b",
                            "company": "DAKO",
                            "cat_num": "C8-ABC",
                            "lot_num": "3983272",
                            "staining_order": 2,
                            "fluor_wavelength": 520,
                            "primary_ab_dilution": "1:5000",
                            "dilutent": "DV",
                            "fluor_dilution": "1:100",
                            "antigen_retrieval_time": "00:01:00",
                            "primary_incubation_time": "00:01:00",
                            "amplification_time": "00:01:00",
                        },
                        {
                            "antibody": "PD-L1",
                            "export_name": "PD-L1 (Opal 200)",
                            "clone": "9A11",
                            "company": "CST",
                            "cat_num": "9A-ABC",
                            "lot_num": "29387234",
                            "staining_order": 3,
                            "fluor_wavelength": 540,
                            "primary_ab_dilution": "1:5000",
                            "dilutent": "VENTANA",
                            "fluor_dilution": "1:200",
                            "antigen_retrieval_time": "00:01:00",
                            "primary_incubation_time": "00:01:00",
                            "amplification_time": "00:01:00",
                        },
                    ],
                    "records": [
                        {
                            "cimac_id": "CTTTPP111.00",
                            "files": {
                                "regions_of_interest": [
                                    {
                                        "roi_id": "1",
                                        "composite_image": {
                                            "upload_placeholder": "6aaaaaaa-047f-4df6-b614-871289a1a2a"
                                        },
                                        "im3": {
                                            "upload_placeholder": "7aaaaaaa-047f-4df6-b614-871289a1a2a"
                                        },
                                        "component_data": {
                                            "upload_placeholder": "8aaaaaaa-047f-4df6-b614-871289a1a2a"
                                        },
                                        "exports": [
                                            {
                                                "export_id": "CD4",
                                                "binary_seg_maps": {
                                                    "upload_placeholder": "1aaaaaaa-047f-4df6-b614-871289a1a2a"
                                                },
                                                "cell_seg_data": {
                                                    "upload_placeholder": "2aaaaaaa-047f-4df6-b614-871289a1a2a"
                                                },
                                                "cell_seg_data_summary": {
                                                    "upload_placeholder": "3aaaaaaa-047f-4df6-b614-871289a1a2a"
                                                },
                                                "tissue_seg_data": {
                                                    "upload_placeholder": "2zaaaaaa-047f-4df6-b614-871289a1a2a"
                                                },
                                                "tissue_seg_data_summary": {
                                                    "upload_placeholder": "3zaaaaaa-047f-4df6-b614-871289a1a2a"
                                                },
                                                "phenotype_map": {
                                                    "upload_placeholder": "4aaaaaaa-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_all_seg": {
                                                    "upload_placeholder": "4aaaaaab-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_cell_seg_map": {
                                                    "upload_placeholder": "4aaaaabb-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_phenotype_map": {
                                                    "upload_placeholder": "4aaaabbb-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_tissue_seg": {
                                                    "upload_placeholder": "4aaabbbb-047f-4df6-b614-871289a1a2a"
                                                },
                                                "score_data": [
                                                    {
                                                        "upload_placeholder": "5aaaaaa1-047f-4df6-b614-871289a1a2a"
                                                    },
                                                    {
                                                        "upload_placeholder": "5aaaaaa2-047f-4df6-b614-871289a1a2a"
                                                    },
                                                ],
                                            },
                                            {
                                                "export_id": "CD8",
                                                "binary_seg_maps": {
                                                    "upload_placeholder": "1aaaaaaa-047f-4df6-b614-871289a1a2b"
                                                },
                                                "cell_seg_data": {
                                                    "upload_placeholder": "2aaaaaaa-047f-4df6-b614-871289a1a2b"
                                                },
                                                "cell_seg_data_summary": {
                                                    "upload_placeholder": "3aaaaaaa-047f-4df6-b614-871289a1a2b"
                                                },
                                                "tissue_seg_data": {
                                                    "upload_placeholder": "2zaaaaaa-047f-4df6-b614-871289a1a2b"
                                                },
                                                "tissue_seg_data_summary": {
                                                    "upload_placeholder": "3zaaaaaa-047f-4df6-b614-871289a1a2b"
                                                },
                                                "phenotype_map": {
                                                    "upload_placeholder": "4aaaaaaa-047f-4df6-b614-871289a1a2b"
                                                },
                                                "image_with_all_seg": {
                                                    "upload_placeholder": "4aaaaaab-047f-4df6-b614-871289a1a2b"
                                                },
                                                "image_with_cell_seg_map": {
                                                    "upload_placeholder": "4aaaaabb-047f-4df6-b614-871289a1a2b"
                                                },
                                                "image_with_phenotype_map": {
                                                    "upload_placeholder": "4aaaabbb-047f-4df6-b614-871289a1a2b"
                                                },
                                                "image_with_tissue_seg": {
                                                    "upload_placeholder": "4aaabbbb-047f-4df6-b614-871289a1a2b"
                                                },
                                                "score_data": [
                                                    {
                                                        "upload_placeholder": "5aaaaaa1-047f-4df6-b614-871289a1a2b"
                                                    },
                                                    {
                                                        "upload_placeholder": "5aaaaaa2-047f-4df6-b614-871289a1a2b"
                                                    },
                                                ],
                                            },
                                        ],
                                    }
                                ]
                            },
                        },
                        {
                            "cimac_id": "CTTTPP121.00",
                            "files": {
                                "regions_of_interest": [
                                    {
                                        "roi_id": "1",
                                        "composite_image": {
                                            "upload_placeholder": "6bbbbbbb-047f-4df6-b614-871289a1a2a"
                                        },
                                        "im3": {
                                            "upload_placeholder": "7bbbbbbb-047f-4df6-b614-871289a1a2a"
                                        },
                                        "component_data": {
                                            "upload_placeholder": "8bbbbbbb-047f-4df6-b614-871289a1a2a"
                                        },
                                        "exports": [
                                            {
                                                "export_id": "CD4",
                                                "binary_seg_maps": {
                                                    "upload_placeholder": "1bbbbbbb-047f-4df6-b614-871289a1a2a"
                                                },
                                                "cell_seg_data": {
                                                    "upload_placeholder": "2bbbbbbb-047f-4df6-b614-871289a1a2a"
                                                },
                                                "cell_seg_data_summary": {
                                                    "upload_placeholder": "3bbbbbbb-047f-4df6-b614-871289a1a2a"
                                                },
                                                "tissue_seg_data": {
                                                    "upload_placeholder": "2abbbbbb-047f-4df6-b614-871289a1a2a"
                                                },
                                                "tissue_seg_data_summary": {
                                                    "upload_placeholder": "3abbbbbb-047f-4df6-b614-871289a1a2a"
                                                },
                                                "phenotype_map": {
                                                    "upload_placeholder": "4bbbbbbb-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_all_seg": {
                                                    "upload_placeholder": "4bbbbbba-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_cell_seg_map": {
                                                    "upload_placeholder": "4bbbbbaa-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_phenotype_map": {
                                                    "upload_placeholder": "4bbbbaaa-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_tissue_seg": {
                                                    "upload_placeholder": "4bbbaaaa-047f-4df6-b614-871289a1a2a"
                                                },
                                                "score_data": [
                                                    {
                                                        "upload_placeholder": "5bbbbbbb-047f-4df6-b614-871289a1a2a"
                                                    }
                                                ],
                                            }
                                        ],
                                    },
                                    {
                                        "roi_id": "2",
                                        "composite_image": {
                                            "upload_placeholder": "6ccccccc-047f-4df6-b614-871289a1a2a"
                                        },
                                        "im3": {
                                            "upload_placeholder": "7ccccccc-047f-4df6-b614-871289a1a2a"
                                        },
                                        "component_data": {
                                            "upload_placeholder": "8ccccccc-047f-4df6-b614-871289a1a2a"
                                        },
                                        "exports": [
                                            {
                                                "export_id": "CD4",
                                                "binary_seg_maps": {
                                                    "upload_placeholder": "1ccccccc-047f-4df6-b614-871289a1a2a"
                                                },
                                                "cell_seg_data": {
                                                    "upload_placeholder": "2ccccccc-047f-4df6-b614-871289a1a2a"
                                                },
                                                "cell_seg_data_summary": {
                                                    "upload_placeholder": "3ccccccc-047f-4df6-b614-871289a1a2a"
                                                },
                                                "tissue_seg_data": {
                                                    "upload_placeholder": "2acccccc-047f-4df6-b614-871289a1a2a"
                                                },
                                                "tissue_seg_data_summary": {
                                                    "upload_placeholder": "3acccccc-047f-4df6-b614-871289a1a2a"
                                                },
                                                "phenotype_map": {
                                                    "upload_placeholder": "4ccccccc-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_all_seg": {
                                                    "upload_placeholder": "4bbbbbbc-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_cell_seg_map": {
                                                    "upload_placeholder": "4bbbbbcc-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_phenotype_map": {
                                                    "upload_placeholder": "4bbbbccc-047f-4df6-b614-871289a1a2a"
                                                },
                                                "image_with_tissue_seg": {
                                                    "upload_placeholder": "4bbbcccc-047f-4df6-b614-871289a1a2a"
                                                },
                                                "score_data": [
                                                    {
                                                        "upload_placeholder": "5ccccccc-047f-4df6-b614-871289a1a2a"
                                                    }
                                                ],
                                            }
                                        ],
                                    },
                                ]
                            },
                        },
                    ],
                    "assay_creator": "DFCI",
                    "slide_scanner_model": "Hamamatsu",
                    "image_analysis_software": "InForm",
                    "image_analysis_software_version": "2.4.2",
                    "cell_segmentation_model": "proprietary",
                    "positive_cell_detection": "proprietary",
                    "staining": "Bond RX",
                    "staining_date": "2001-01-01 00:00:00",
                    "imaging_date": "2001-01-01 00:00:00",
                    "imaging_status": "Yes",
                }
            ]
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="111/1_score_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/score_data_0.txt",
            upload_placeholder="5aaaaaa1-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111_extra/1_score_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/score_data_1.txt",
            upload_placeholder="5aaaaaa2-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD4/binary_seg_maps.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/binary_seg_maps.tif",
            upload_placeholder="1aaaaaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD4/cell_seg_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/cell_seg_data.txt",
            upload_placeholder="2aaaaaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD4/cell_seg_data_summary.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/cell_seg_data_summary.txt",
            upload_placeholder="3aaaaaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD4/tissue_seg_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/tissue_seg_data.txt",
            upload_placeholder="2zaaaaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD4/tissue_seg_data_summary.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/tissue_seg_data_summary.txt",
            upload_placeholder="3zaaaaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD4/phenotype_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/phenotype_map.tif",
            upload_placeholder="4aaaaaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD4/image_with_all_seg.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/image_with_all_seg.tif",
            upload_placeholder="4aaaaaab-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD4/image_with_cell_seg_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/image_with_cell_seg_map.tif",
            upload_placeholder="4aaaaabb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD4/image_with_phenotype_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/image_with_phenotype_map.tif",
            upload_placeholder="4aaaabbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD4/image_with_tissue_seg.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD4/image_with_tissue_seg.tif",
            upload_placeholder="4aaabbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1_composite_image.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/composite_image.tif",
            upload_placeholder="6aaaaaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1.im3",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/multispectral.im3",
            upload_placeholder="7aaaaaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1_component_data.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/component_data.tif",
            upload_placeholder="8aaaaaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1_score_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/score_data_0.txt",
            upload_placeholder="5aaaaaa1-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111_extra/1_score_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/score_data_1.txt",
            upload_placeholder="5aaaaaa2-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD8/binary_seg_maps.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/binary_seg_maps.tif",
            upload_placeholder="1aaaaaaa-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD8/cell_seg_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/cell_seg_data.txt",
            upload_placeholder="2aaaaaaa-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD8/cell_seg_data_summary.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/cell_seg_data_summary.txt",
            upload_placeholder="3aaaaaaa-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD8/tissue_seg_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/tissue_seg_data.txt",
            upload_placeholder="2zaaaaaa-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD8/tissue_seg_data_summary.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/tissue_seg_data_summary.txt",
            upload_placeholder="3zaaaaaa-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD8/phenotype_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/phenotype_map.tif",
            upload_placeholder="4aaaaaaa-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD8/image_with_all_seg.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/image_with_all_seg.tif",
            upload_placeholder="4aaaaaab-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD8/image_with_cell_seg_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/image_with_cell_seg_map.tif",
            upload_placeholder="4aaaaabb-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD8/image_with_phenotype_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/image_with_phenotype_map.tif",
            upload_placeholder="4aaaabbb-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="111/1/CD8/image_with_tissue_seg.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP111.00/roi_1/CD8/image_with_tissue_seg.tif",
            upload_placeholder="4aaabbbb-047f-4df6-b614-871289a1a2b",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1/CD4/binary_seg_maps.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/binary_seg_maps.tif",
            upload_placeholder="1bbbbbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1/CD4/cell_seg_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/cell_seg_data.txt",
            upload_placeholder="2bbbbbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1/CD4/cell_seg_data_summary.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/cell_seg_data_summary.txt",
            upload_placeholder="3bbbbbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1/CD4/tissue_seg_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/tissue_seg_data.txt",
            upload_placeholder="2abbbbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1/CD4/tissue_seg_data_summary.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/tissue_seg_data_summary.txt",
            upload_placeholder="3abbbbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1/CD4/phenotype_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/phenotype_map.tif",
            upload_placeholder="4bbbbbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1/CD4/image_with_all_seg.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/image_with_all_seg.tif",
            upload_placeholder="4bbbbbba-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1/CD4/image_with_cell_seg_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/image_with_cell_seg_map.tif",
            upload_placeholder="4bbbbbaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1/CD4/image_with_phenotype_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/image_with_phenotype_map.tif",
            upload_placeholder="4bbbbaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1/CD4/image_with_tissue_seg.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/image_with_tissue_seg.tif",
            upload_placeholder="4bbbaaaa-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1_score_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/CD4/score_data_0.txt",
            upload_placeholder="5bbbbbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1_composite_image.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/composite_image.tif",
            upload_placeholder="6bbbbbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1.im3",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/multispectral.im3",
            upload_placeholder="7bbbbbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/1_component_data.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_1/component_data.tif",
            upload_placeholder="8bbbbbbb-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2/CD4/binary_seg_maps.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/binary_seg_maps.tif",
            upload_placeholder="1ccccccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2/CD4/cell_seg_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/cell_seg_data.txt",
            upload_placeholder="2ccccccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2/CD4/cell_seg_data_summary.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/cell_seg_data_summary.txt",
            upload_placeholder="3ccccccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2/CD4/tissue_seg_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/tissue_seg_data.txt",
            upload_placeholder="2acccccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2/CD4/tissue_seg_data_summary.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/tissue_seg_data_summary.txt",
            upload_placeholder="3acccccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2/CD4/phenotype_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/phenotype_map.tif",
            upload_placeholder="4ccccccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2/CD4/image_with_all_seg.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/image_with_all_seg.tif",
            upload_placeholder="4bbbbbbc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2/CD4/image_with_cell_seg_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/image_with_cell_seg_map.tif",
            upload_placeholder="4bbbbbcc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2/CD4/image_with_phenotype_map.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/image_with_phenotype_map.tif",
            upload_placeholder="4bbbbccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2/CD4/image_with_tissue_seg.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/image_with_tissue_seg.tif",
            upload_placeholder="4bbbcccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2_score_data.txt",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/CD4/score_data_0.txt",
            upload_placeholder="5ccccccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2_composite_image.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/composite_image.tif",
            upload_placeholder="6ccccccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2.im3",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/multispectral.im3",
            upload_placeholder="7ccccccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="121/2_component_data.tif",
            gs_key="test_prism_trial_id/mif/CTTTPP121.00/roi_2/component_data.tif",
            upload_placeholder="8ccccccc-047f-4df6-b614-871289a1a2a",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["mif"]
        for record in batch["records"]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@assay_data_generator
def nanostring() -> PrismTestData:
    upload_type = "nanostring"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "test_prism_trial_id",
        "assays": {
            "nanostring": [
                {
                    "assay_creator": "DFCI",
                    "batch_id": "test_batch",
                    "data": {
                        "raw": {
                            "upload_placeholder": "d658b480-ed78-4717-b622-3e84bde632b6"
                        },
                        "normalized": {
                            "upload_placeholder": "4e9d0a47-90dc-4134-9ad6-3e3dd83619d6"
                        },
                    },
                    "runs": [
                        {
                            "run_id": "RUN01",
                            "control_raw_rcc": {
                                "upload_placeholder": "1b0b3b8f-6417-4a37-85dc-e8aa75594678"
                            },
                            "samples": [
                                {
                                    "cimac_id": "CTTTPP111.00",
                                    "raw_rcc": {
                                        "upload_placeholder": "9855c579-82e0-42ee-8225-7c1c736bb69f"
                                    },
                                },
                                {
                                    "cimac_id": "CTTTPP112.00",
                                    "raw_rcc": {
                                        "upload_placeholder": "9855c579-82e0-42ee-8225-7c1c736bb69g"
                                    },
                                },
                            ],
                        },
                        {
                            "run_id": "RUN02",
                            "control_raw_rcc": {
                                "upload_placeholder": "1b0b3b8f-6417-4a37-85dc-e8aa75594679"
                            },
                            "samples": [
                                {
                                    "cimac_id": "CTTTPP111.00",
                                    "raw_rcc": {
                                        "upload_placeholder": "9855c579-82e0-42ee-8225-7c1c736bb69h"
                                    },
                                }
                            ],
                        },
                    ],
                }
            ]
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="raw_data.csv",
            upload_placeholder="d658b480-ed78-4717-b622-3e84bde632b6",
            gs_key="test_prism_trial_id/nanostring/test_batch/raw_data.csv",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="normalized.csv",
            upload_placeholder="4e9d0a47-90dc-4134-9ad6-3e3dd83619d6",
            gs_key="test_prism_trial_id/nanostring/test_batch/normalized_data.csv",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="RUN01_reference.rcc",
            upload_placeholder="1b0b3b8f-6417-4a37-85dc-e8aa75594678",
            gs_key="test_prism_trial_id/nanostring/test_batch/RUN01/control.rcc",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="RUN01_111.rcc",
            upload_placeholder="9855c579-82e0-42ee-8225-7c1c736bb69f",
            gs_key="test_prism_trial_id/nanostring/test_batch/RUN01/CTTTPP111.00.rcc",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="RUN01_112.rcc",
            upload_placeholder="9855c579-82e0-42ee-8225-7c1c736bb69g",
            gs_key="test_prism_trial_id/nanostring/test_batch/RUN01/CTTTPP112.00.rcc",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="RUN02_reference.rcc",
            upload_placeholder="1b0b3b8f-6417-4a37-85dc-e8aa75594679",
            gs_key="test_prism_trial_id/nanostring/test_batch/RUN02/control.rcc",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="RUN02_111.rcc",
            upload_placeholder="9855c579-82e0-42ee-8225-7c1c736bb69h",
            gs_key="test_prism_trial_id/nanostring/test_batch/RUN02/CTTTPP111.00.rcc",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        sample["cimac_id"]
        for batch in prismify_patch["assays"]["nanostring"]
        for runs in batch["runs"]
        for sample in runs["samples"]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "assays")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


missing = set(SUPPORTED_ASSAYS).difference([f.__name__ for f in assay_data_generators])
assert not missing, f"Missing assay test data generators for {missing}"
