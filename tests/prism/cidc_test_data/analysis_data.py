from copy import deepcopy

from cidc_schemas.prism import SUPPORTED_ANALYSES

from .assay_data import cytof, tcr_fastq

from .utils import (
    copy_dict_with_branch,
    get_prismify_args,
    get_test_trial,
    LocalFileUploadEntry,
    PrismTestData,
)

analysis_data_generators = []


def analysis_data_generator(f):
    analysis_data_generators.append(f)
    return f


@analysis_data_generator
def wes_analysis() -> PrismTestData:
    upload_type = "wes_analysis"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "analysis": {
            "wes_analysis": {
                "pair_runs": [
                    {
                        "run_id": "run_1",
                        "comments": "a comment",
                        "error": {
                            "upload_placeholder": "cdef9e1e-8e04-46ed-a9e6-bb618188a6d7"
                        },
                        "clonality": {
                            "clonality_input": {
                                "upload_placeholder": "cdef9e1e-8e04-46ed-a9e6-bb618188a6d6"
                            },
                            "clonality_results": {
                                "upload_placeholder": "ctef9e1e-8e04-46ed-a9e6-bb618188a6d6"
                            },
                            "clonality_summary": {
                                "upload_placeholder": "dtef9e1e-8e04-46ed-a9e6-bb618188a6d6"
                            },
                        },
                        "msisensor": {
                            "msisensor": {
                                "upload_placeholder": "msi18d7a-fd96-4e75-b265-1590c703a301"
                            }
                        },
                        "copynumber": {
                            "copynumber_segments": {
                                "upload_placeholder": "85989077-49e4-44c6-8788-3b19357d3122"
                            },
                            "copynumber_genome_view": {
                                "upload_placeholder": "eb1a8d7a-fd96-4e75-b265-1590c703a301"
                            },
                            "copynumber_chromosome_view": {
                                "upload_placeholder": "fb1a8d7a-fd96-4e75-b265-1590c703a301"
                            },
                            "copynumber_sequenza_gainloss": {
                                "upload_placeholder": "gb1a8d7a-fd96-4e75-b265-1590c703a301"
                            },
                            "copynumber_sequenza_final": {
                                "upload_placeholder": "hb1a8d7a-fd96-4e75-b265-1590c703a301"
                            },
                            "copynumber_consensus": {
                                "upload_placeholder": "ib1a8d7a-fd96-4e75-b265-1590c703a301"
                            },
                            "copynumber_consensus_gain": {
                                "upload_placeholder": "jb1a8d7a-fd96-4e75-b265-1590c703a301"
                            },
                            "copynumber_consensus_loss": {
                                "upload_placeholder": "kb1a8d7a-fd96-4e75-b265-1590c703a301"
                            },
                            "copynumber_facets": {
                                "upload_placeholder": "lb1a8d7a-fd96-4e75-b265-1590c703a301"
                            },
                            "copynumber_facets_gainloss": {
                                "upload_placeholder": "mb1a8d7a-fd96-4e75-b265-1590c703a301"
                            },
                            "copynumber_cnv_segments": {
                                "upload_placeholder": "etef9e1e-8e04-46ed-a9e6-bb618188a6d6"
                            },
                            "copynumber_cnv_segments_enhanced": {
                                "upload_placeholder": "ftef9e1e-8e04-46ed-a9e6-bb618188a6d6"
                            },
                            "copynumber_cnv_scatterplot": {
                                "upload_placeholder": "gtef9e1e-8e04-46ed-a9e6-bb618188a6d6"
                            },
                            "copynumber_cnvkit_gainloss": {
                                "upload_placeholder": "htef9e1e-8e04-46ed-a9e6-bb618188a6d6"
                            },
                        },
                        "neoantigen": {
                            "combined_filtered": {
                                "upload_placeholder": "f47271fb-e2c7-5436-cafe-5cf84bc72bf7"
                            },
                        },
                        "purity": {
                            "optimal_purity_value": {
                                "upload_placeholder": "f0b85ef8-47cb-45b9-bb94-c961150786b9"
                            },
                            "cp_contours": {
                                "upload_placeholder": "b86ab142-a925-433c-bb13-030c0684365e"
                            },
                            "alternative_solutions": {
                                "upload_placeholder": "c86ab142-a925-433c-bb13-030c0684365e"
                            },
                        },
                        "report": {
                            "config": {
                                "upload_placeholder": "abc271fb-d2c7-4436-bafe-4cf84bc72bf4"
                            },
                            "wes_run_version": {
                                "upload_placeholder": "c47271fb-e2c7-5436-cafe-5cf84bc72bf4"
                            },
                            "tumor_germline_overlap": {
                                "upload_placeholder": "d47271fb-e2c7-5436-cafe-5cf84bc72bf5"
                            },
                            "metasheet": {
                                "upload_placeholder": "xyz271fb-e2c7-5436-cafe-5cf84bc72bf4"
                            },
                            "report": {
                                "upload_placeholder": "yyz271fb-e2c7-5436-cafe-5cf84bc72bf5"
                            },
                            "wes_sample_json": {
                                "upload_placeholder": "yyz24763-fb9f-58b4-c7c4-8175759933s1"
                            },
                        },
                        "rna": {
                            "haplotyper": {
                                "upload_placeholder": "e0b85ef8-47cb-45b9-bb94-c961150786b9"
                            },
                            "vcf_tnscope_filter_neoantigen": {
                                "upload_placeholder": "d0b85ef8-47cb-45b9-bb94-c961150786b9"
                            },
                        },
                        "somatic": {
                            "vcf_gz_tnscope_output": {
                                "upload_placeholder": "c86ab142-a925-433c-bb13-030c0684365f"
                            },
                            "tnscope_output_twist_vcf": {
                                "upload_placeholder": "99966c04-86f8-44af-953d-0cfb10d11b99"
                            },
                            "tnscope_output_twist_maf": {
                                "upload_placeholder": "66689bba-708c-449f-879f-44cba199c666"
                            },
                            "tnscope_output_twist_filtered_vcf": {
                                "upload_placeholder": "88866c04-86f8-44af-953d-0cfb10d11b88"
                            },
                            "tnscope_output_twist_filtered_maf": {
                                "upload_placeholder": "777b8502-d7cc-4002-a96d-57e635f4f277"
                            },
                        },
                        "tcell": {
                            "tcellextrect": {
                                "upload_placeholder": "653bd098-3997-494b-8db9-03d114b3fbb3"
                            }
                        },
                        "tumor": {
                            "cimac_id": "CTTTPP111.00",
                            "alignment": {
                                "align_sorted_dedup": {
                                    "upload_placeholder": "2068ae50-3ce7-4b0c-ba56-f678233dd098"
                                },
                                "align_sorted_dedup_index": {
                                    "upload_placeholder": "cc4ce43e-bc4f-4a93-b482-454f874421a8"
                                },
                                "align_recalibrated": {
                                    "upload_placeholder": "dc4ce43e-bc4f-4a93-b482-454f874421a8"
                                },
                                "align_recalibrated_index": {
                                    "upload_placeholder": "ec4ce43e-bc4f-4a93-b482-454f874421a8"
                                },
                            },
                            "germline": {
                                "haplotyper_targets": {
                                    "upload_placeholder": "ht899d73-7373-4041-85f9-6cc4324be811"
                                },
                                "haplotyper_output": {
                                    "upload_placeholder": "it899d73-7373-4041-85f9-6cc4324be811"
                                },
                            },
                            "hla": {
                                "hla_final_result": {
                                    "upload_placeholder": "218be905-220d-417f-8395-0de84fcd81sg"
                                },
                                "optitype_result": {
                                    "upload_placeholder": "a5899d73-7373-4041-85f9-6cc4324be817"
                                },
                                "xhla_report_hla": {
                                    "upload_placeholder": "2f3307bd-960e-4735-b831-f93d20fe8d37"
                                },
                            },
                        },
                        "normal": {
                            "cimac_id": "CTTTPP111.00",
                            "alignment": {
                                "align_sorted_dedup": {
                                    "upload_placeholder": "c163f7aa-43ba-40f4-b11d-bddb79b41763"
                                },
                                "align_sorted_dedup_index": {
                                    "upload_placeholder": "be406c27-2ef4-477c-93e5-684fbe4f9307"
                                },
                                "align_recalibrated": {
                                    "upload_placeholder": "d163f7aa-43ba-40f4-b11d-bddb79b41763"
                                },
                                "align_recalibrated_index": {
                                    "upload_placeholder": "ce406c27-2ef4-477c-93e5-684fbe4f9307"
                                },
                            },
                            "hla": {
                                "hla_final_result": {
                                    "upload_placeholder": "7b36da9d-c015-42be-80df-d22c17a29124"
                                },
                                "optitype_result": {
                                    "upload_placeholder": "6b36da9d-c015-42be-80df-d22c17a29124"
                                },
                                "xhla_report_hla": {
                                    "upload_placeholder": "f6a76030-cf27-41e6-8836-17c99479001e"
                                },
                            },
                            "germline": {
                                "haplotyper_targets": {
                                    "upload_placeholder": "ht899d73-7373-4041-85f9-6cc4324be812"
                                },
                                "haplotyper_output": {
                                    "upload_placeholder": "it899d73-7373-4041-85f9-6cc4324be812"
                                },
                            },
                        },
                    },
                    {
                        "run_id": "run_2",
                        "error": {
                            "upload_placeholder": "a4cba177-0be5-4d7d-b635-4a60adaa9576"
                        },
                        "clonality": {
                            "clonality_input": {
                                "upload_placeholder": "a4cba177-0be5-4d7d-b635-4a60adaa9575"
                            },
                            "clonality_results": {
                                "upload_placeholder": "aucba177-0be5-4d7d-b635-4a60adaa9575"
                            },
                            "clonality_summary": {
                                "upload_placeholder": "b4cba177-0be5-4d7d-b635-4a60adaa9575"
                            },
                        },
                        "msisensor": {
                            "msisensor": {
                                "upload_placeholder": "msi28d7a-fd96-4e75-b265-1590c703a301"
                            }
                        },
                        "copynumber": {
                            "copynumber_segments": {
                                "upload_placeholder": "c187bcfe-b454-46a5-bf85-e2a2d5f7a9a5"
                            },
                            "copynumber_genome_view": {
                                "upload_placeholder": "ba2984c0-f7e6-470c-95ef-e4b33cbdea48"
                            },
                            "copynumber_chromosome_view": {
                                "upload_placeholder": "d187bcfe-b454-46a5-bf85-e2a2d5f7a9a5"
                            },
                            "copynumber_sequenza_gainloss": {
                                "upload_placeholder": "ca2984c0-f7e6-470c-95ef-e4b33cbdea48"
                            },
                            "copynumber_sequenza_final": {
                                "upload_placeholder": "e187bcfe-b454-46a5-bf85-e2a2d5f7a9a5"
                            },
                            "copynumber_consensus": {
                                "upload_placeholder": "f187bcfe-b454-46a5-bf85-e2a2d5f7a9a5"
                            },
                            "copynumber_consensus_gain": {
                                "upload_placeholder": "da2984c0-f7e6-470c-95ef-e4b33cbdea48"
                            },
                            "copynumber_consensus_loss": {
                                "upload_placeholder": "g187bcfe-b454-46a5-bf85-e2a2d5f7a9a5"
                            },
                            "copynumber_facets": {
                                "upload_placeholder": "ea2984c0-f7e6-470c-95ef-e4b33cbdea48"
                            },
                            "copynumber_facets_gainloss": {
                                "upload_placeholder": "h187bcfe-b454-46a5-bf85-e2a2d5f7a9a5"
                            },
                            "copynumber_cnv_segments": {
                                "upload_placeholder": "bucba177-0be5-4d7d-b635-4a60adaa9575"
                            },
                            "copynumber_cnv_segments_enhanced": {
                                "upload_placeholder": "c4cba177-0be5-4d7d-b635-4a60adaa9575"
                            },
                            "copynumber_cnv_scatterplot": {
                                "upload_placeholder": "cucba177-0be5-4d7d-b635-4a60adaa9575"
                            },
                            "copynumber_cnvkit_gainloss": {
                                "upload_placeholder": "d4cba177-0be5-4d7d-b635-4a60adaa9575"
                            },
                        },
                        "neoantigen": {
                            "combined_filtered": {
                                "upload_placeholder": "86824763-fb9f-58b4-c7c4-8175759933f7"
                            },
                        },
                        "somatic": {
                            "vcf_gz_tnscope_output": {
                                "upload_placeholder": "84466c04-86f8-44af-953d-0cfb10d11b36"
                            },
                            "tnscope_output_twist_vcf": {
                                "upload_placeholder": "64466c04-86f8-44af-953d-0cfb10d11b34"
                            },
                            "tnscope_output_twist_maf": {
                                "upload_placeholder": "66589bba-708c-449f-879f-44cba199c666"
                            },
                            "tnscope_output_twist_filtered_vcf": {
                                "upload_placeholder": "88466c04-86f8-44af-953d-0cfb10d11b88"
                            },
                            "tnscope_output_twist_filtered_maf": {
                                "upload_placeholder": "773b8502-d7cc-4002-a96d-57e635f4f277"
                            },
                        },
                        "purity": {
                            "alternative_solutions": {
                                "upload_placeholder": "98621828-ee22-40d1-840a-0dae97e8bf09"
                            },
                            "cp_contours": {
                                "upload_placeholder": "08621828-ee22-40d1-840a-0dae97e8bf09"
                            },
                            "optimal_purity_value": {
                                "upload_placeholder": "76824763-fb9f-58b4-c7c4-8175759933f6"
                            },
                        },
                        "rna": {
                            "haplotyper": {
                                "upload_placeholder": "88621828-ee22-40d1-840a-0dae97e8bf09"
                            },
                            "vcf_tnscope_filter_neoantigen": {
                                "upload_placeholder": "78621828-ee22-40d1-840a-0dae97e8bf09"
                            },
                        },
                        "report": {
                            "config": {
                                "upload_placeholder": "abc24763-fb9f-48b4-b7c4-7175759933f5"
                            },
                            "wes_run_version": {
                                "upload_placeholder": "56824763-fb9f-58b4-c7c4-8175759933f4"
                            },
                            "tumor_germline_overlap": {
                                "upload_placeholder": "66824763-fb9f-58b4-c7c4-8175759933f5"
                            },
                            "metasheet": {
                                "upload_placeholder": "xyz24763-fb9f-58b4-c7c4-8175759933f4"
                            },
                            "report": {
                                "upload_placeholder": "yyz24763-fb9f-58b4-c7c4-8175759933f5"
                            },
                            "wes_sample_json": {
                                "upload_placeholder": "yyz271fb-e2c7-5436-cafe-5cf84bc72bs2"
                            },
                        },
                        "tcell": {
                            "tcellextrect": {
                                "upload_placeholder": "1d589bba-708c-449f-879f-44cba199c635"
                            }
                        },
                        "tumor": {
                            "cimac_id": "CTTTPP121.00",
                            "alignment": {
                                "align_sorted_dedup": {
                                    "upload_placeholder": "d23d0858-eabb-4e9d-ad42-9bb4edadfd59"
                                },
                                "align_sorted_dedup_index": {
                                    "upload_placeholder": "ea9a388b-d679-4a77-845f-2c4073425128"
                                },
                                "align_recalibrated": {
                                    "upload_placeholder": "e23d0858-eabb-4e9d-ad42-9bb4edadfd59"
                                },
                                "align_recalibrated_index": {
                                    "upload_placeholder": "fa9a388b-d679-4a77-845f-2c4073425128"
                                },
                            },
                            "germline": {
                                "haplotyper_output": {
                                    "upload_placeholder": "it899d73-7373-4041-85f9-6cc4324be813"
                                },
                                "haplotyper_targets": {
                                    "upload_placeholder": "ht899d73-7373-4041-85f9-6cc4324be813"
                                },
                            },
                            "hla": {
                                "hla_final_result": {
                                    "upload_placeholder": "84f6bd4c-00db-4ce3-a6b6-a8482a3332sg"
                                },
                                "optitype_result": {
                                    "upload_placeholder": "671d710e-f245-4d2b-8732-2774e26aec10"
                                },
                                "xhla_report_hla": {
                                    "upload_placeholder": "4807aaa5-bafa-4fe5-89e9-73f9d734b971"
                                },
                            },
                        },
                        "normal": {
                            "cimac_id": "CTTTPP121.00",
                            "alignment": {
                                "align_sorted_dedup": {
                                    "upload_placeholder": "f2b13d18-36a2-4273-a69c-a143415231db"
                                },
                                "align_sorted_dedup_index": {
                                    "upload_placeholder": "4a06b799-2eb8-47f3-92fa-f5e21da85697"
                                },
                                "align_recalibrated": {
                                    "upload_placeholder": "g2b13d18-36a2-4273-a69c-a143415231db"
                                },
                                "align_recalibrated_index": {
                                    "upload_placeholder": "5a06b799-2eb8-47f3-92fa-f5e21da85697"
                                },
                            },
                            "germline": {
                                "haplotyper_targets": {
                                    "upload_placeholder": "ht899d73-7373-4041-85f9-6cc4324be814"
                                },
                                "haplotyper_output": {
                                    "upload_placeholder": "it899d73-7373-4041-85f9-6cc4324be814"
                                },
                            },
                            "hla": {
                                "hla_final_result": {
                                    "upload_placeholder": "0371d710-e3d0-4d1b-b87f-23bbadc4ae7e"
                                },
                                "optitype_result": {
                                    "upload_placeholder": "9371d710-e3d0-4d1b-b87f-23bbadc4ae7e"
                                },
                                "xhla_report_hla": {
                                    "upload_placeholder": "1d0c1f42-6a58-4e4b-b127-208c33f2aeb6"
                                },
                            },
                        },
                    },
                ],
                "excluded_samples": [
                    {"cimac_id": "CTTTPP111.00", "reason_excluded": "low coverage"},
                    {"cimac_id": "CTTTPP122.00", "reason_excluded": "module failed"},
                ],
            }
        },
        "protocol_identifier": "test_prism_trial_id",
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="gs://results/analysis/run_1_error.yaml",
            gs_key="test_prism_trial_id/wes/run_1/analysis/error.yaml",
            upload_placeholder="cdef9e1e-8e04-46ed-a9e6-bb618188a6d7",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_1/run_1_pyclone6.input.tsv",
            gs_key="test_prism_trial_id/wes/run_1/analysis/clonality_input.tsv",
            upload_placeholder="cdef9e1e-8e04-46ed-a9e6-bb618188a6d6",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_1/run_1_pyclone6.results.tsv",
            gs_key="test_prism_trial_id/wes/run_1/analysis/clonality_results.tsv",
            upload_placeholder="ctef9e1e-8e04-46ed-a9e6-bb618188a6d6",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_1/run_1_pyclone6.results.summary.tsv",
            upload_placeholder="dtef9e1e-8e04-46ed-a9e6-bb618188a6d6",
            gs_key="test_prism_trial_id/wes/run_1/analysis/clonality_summary.tsv",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_1/run_1.bin50.final.seqz.txt.gz",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_sequenza_final.txt.gz",
            upload_placeholder="hb1a8d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_1/run_1_CP_contours.pdf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/cp_contours.pdf",
            upload_placeholder="b86ab142-a925-433c-bb13-030c0684365e",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_1/run_1_alternative_solutions.txt",
            gs_key="test_prism_trial_id/wes/run_1/analysis/alternative_solutions.txt",
            upload_placeholder="c86ab142-a925-433c-bb13-030c0684365e",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_1/run_1_chromosome_view.pdf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_chromosome_view.pdf",
            upload_placeholder="fb1a8d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_1/run_1_sequenza_gainLoss.bed",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_sequenza_gainloss.bed",
            upload_placeholder="gb1a8d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/cnvkit/run_1/run_1.call.cns",
            upload_placeholder="etef9e1e-8e04-46ed-a9e6-bb618188a6d6",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_cnv_segments.cns",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/cnvkit/run_1/run_1.call.enhanced.cns",
            upload_placeholder="ftef9e1e-8e04-46ed-a9e6-bb618188a6d6",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_cnv_segments_enhanced.cns",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/cnvkit/run_1/run_1.scatter.png",
            upload_placeholder="gtef9e1e-8e04-46ed-a9e6-bb618188a6d6",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_cnv_scatterplot.png",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/cnvkit/run_1/run_1_cnvkit_gainLoss.bed",
            upload_placeholder="htef9e1e-8e04-46ed-a9e6-bb618188a6d6",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_cnvkit_gainloss.bed",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_1/run_1_segments.txt",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_segments.txt",
            upload_placeholder="85989077-49e4-44c6-8788-3b19357d3122",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_1/run_1_genome_view.pdf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_genome_view.pdf",
            upload_placeholder="eb1a8d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/copynumber/run_1/run_1_consensus.bed",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_consensus.bed",
            upload_placeholder="ib1a8d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/copynumber/run_1/run_1_consensus_merged_GAIN.bed",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_consensus_gain.bed",
            upload_placeholder="jb1a8d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/copynumber/run_1/run_1_consensus_merged_LOSS.bed",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_consensus_loss.bed",
            upload_placeholder="kb1a8d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/purity/run_1/run_1.cncf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_facets.cncf",
            upload_placeholder="lb1a8d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/purity/run_1/run_1_facets_gainLoss.bed",
            gs_key="test_prism_trial_id/wes/run_1/analysis/copynumber_facets_gainloss.bed",
            upload_placeholder="mb1a8d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/msisensor2/run_1/run_1_msisensor2.txt",
            gs_key="test_prism_trial_id/wes/run_1/analysis/msisensor.txt",
            upload_placeholder="msi18d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_1/run_1_tnscope.output.vcf.gz",
            gs_key="test_prism_trial_id/wes/run_1/analysis/vcf_gz_tnscope_output.vcf.gz",
            upload_placeholder="c86ab142-a925-433c-bb13-030c0684365f",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_1/run_1_tnscope.output.twist.vcf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tnscope_output_twist.vcf",
            upload_placeholder="99966c04-86f8-44af-953d-0cfb10d11b99",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_1/run_1_tnscope.output.twist.filtered.vcf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tnscope_output_twist_filtered.vcf",
            upload_placeholder="88866c04-86f8-44af-953d-0cfb10d11b88",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_1/run_1_tnscope.output.twist.filtered.maf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tnscope_output_twist_filtered.maf",
            upload_placeholder="777b8502-d7cc-4002-a96d-57e635f4f277",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_1/run_1_tnscope.output.twist.maf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tnscope_output_twist.maf",
            upload_placeholder="66689bba-708c-449f-879f-44cba199c666",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/hlahd/CTTTPP111.00/result/CTTTPP111.00_final.result.txt",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tumor/CTTTPP111.00/hla_final_result.txt",
            upload_placeholder="218be905-220d-417f-8395-0de84fcd81sg",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/purity/run_1/run_1.optimalpurityvalue.txt",
            gs_key="test_prism_trial_id/wes/run_1/analysis/optimal_purity_value.txt",
            upload_placeholder="f0b85ef8-47cb-45b9-bb94-c961150786b9",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/rna/run_1/run_1.haplotyper.rna.vcf.gz",
            gs_key="test_prism_trial_id/wes/run_1/analysis/haplotyper.vcf.gz",
            upload_placeholder="e0b85ef8-47cb-45b9-bb94-c961150786b9",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/rna/run_1/run_1_tnscope.output.twist.neoantigen.vep.rna.vcf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/vcf_tnscope_filter_neoantigen.vcf",
            upload_placeholder="d0b85ef8-47cb-45b9-bb94-c961150786b9",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/config.yaml",
            gs_key="test_prism_trial_id/wes/run_1/analysis/config.yaml",
            upload_placeholder="abc271fb-d2c7-4436-bafe-4cf84bc72bf4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/metasheet.csv",
            gs_key="test_prism_trial_id/wes/run_1/analysis/metasheet.csv",
            upload_placeholder="xyz24763-fb9f-58b4-c7c4-8175759933f4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report.tar.gz",
            gs_key="test_prism_trial_id/wes/run_1/analysis/report.tar.gz",
            upload_placeholder="yyz24763-fb9f-58b4-c7c4-8175759933f5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/json/run_1.wes.json",
            gs_key="test_prism_trial_id/wes/run_1/analysis/wes_sample.json",
            upload_placeholder="yyz24763-fb9f-58b4-c7c4-8175759933s1",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/WES_Meta/02_WES_Run_Version.tsv",
            gs_key="test_prism_trial_id/wes/run_1/analysis/wes_run_version.tsv",
            upload_placeholder="c47271fb-e2c7-5436-cafe-5cf84bc72bf4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/somatic_variants/05_tumor_germline_overlap.tsv",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tumor_germline_overlap.tsv",
            upload_placeholder="d47271fb-e2c7-5436-cafe-5cf84bc72bf5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/neoantigen/run_1/combined/run_1.filtered.tsv",
            gs_key="test_prism_trial_id/wes/run_1/analysis/combined_filtered.tsv",
            upload_placeholder="f47271fb-e2c7-5436-cafe-5cf84bc72bf7",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00.sorted.dedup.bam",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tumor/CTTTPP111.00/sorted.dedup.bam",
            upload_placeholder="2068ae50-3ce7-4b0c-ba56-f678233dd098",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00.sorted.dedup.bam.bai",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tumor/CTTTPP111.00/sorted.dedup.bam.bai",
            upload_placeholder="cc4ce43e-bc4f-4a93-b482-454f874421a8",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00_recalibrated.bam",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tumor/CTTTPP111.00/recalibrated.bam",
            upload_placeholder="dc4ce43e-bc4f-4a93-b482-454f874421a8",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00_recalibrated.bam.bai",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tumor/CTTTPP111.00/recalibrated.bam.bai",
            upload_placeholder="ec4ce43e-bc4f-4a93-b482-454f874421a8",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/tcellextrect/run_1/run_1_tcellextrect.txt",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tcellextrect.txt",
            upload_placeholder="653bd098-3997-494b-8db9-03d114b3fbb3",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/germline/CTTTPP111.00/CTTTPP111.00_haplotyper.targets.vcf.gz",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tumor/CTTTPP111.00/haplotyper_targets.vcf.gz",
            upload_placeholder="ht899d73-7373-4041-85f9-6cc4324be811",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/germline/CTTTPP111.00/CTTTPP111.00_haplotyper.output.vcf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tumor/CTTTPP111.00/haplotyper_output.vcf",
            upload_placeholder="it899d73-7373-4041-85f9-6cc4324be811",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/optitype/CTTTPP111.00/CTTTPP111.00_result.tsv",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tumor/CTTTPP111.00/optitype_result.tsv",
            upload_placeholder="a5899d73-7373-4041-85f9-6cc4324be817",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/xhla/CTTTPP111.00/report-CTTTPP111.00-hla.json",
            gs_key="test_prism_trial_id/wes/run_1/analysis/tumor/CTTTPP111.00/xhla_report_hla.json",
            upload_placeholder="2f3307bd-960e-4735-b831-f93d20fe8d37",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00.sorted.dedup.bam",
            gs_key="test_prism_trial_id/wes/run_1/analysis/normal/CTTTPP111.00/sorted.dedup.bam",
            upload_placeholder="c163f7aa-43ba-40f4-b11d-bddb79b41763",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00.sorted.dedup.bam.bai",
            gs_key="test_prism_trial_id/wes/run_1/analysis/normal/CTTTPP111.00/sorted.dedup.bam.bai",
            upload_placeholder="be406c27-2ef4-477c-93e5-684fbe4f9307",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00_recalibrated.bam",
            gs_key="test_prism_trial_id/wes/run_1/analysis/normal/CTTTPP111.00/recalibrated.bam",
            upload_placeholder="d163f7aa-43ba-40f4-b11d-bddb79b41763",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00_recalibrated.bam.bai",
            gs_key="test_prism_trial_id/wes/run_1/analysis/normal/CTTTPP111.00/recalibrated.bam.bai",
            upload_placeholder="ce406c27-2ef4-477c-93e5-684fbe4f9307",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_2/run_2_alternative_solutions.txt",
            gs_key="test_prism_trial_id/wes/run_2/analysis/alternative_solutions.txt",
            upload_placeholder="98621828-ee22-40d1-840a-0dae97e8bf09",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_2/run_2_CP_contours.pdf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/cp_contours.pdf",
            upload_placeholder="08621828-ee22-40d1-840a-0dae97e8bf09",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/rna/run_2/run_2.haplotyper.rna.vcf.gz",
            gs_key="test_prism_trial_id/wes/run_2/analysis/haplotyper.vcf.gz",
            upload_placeholder="88621828-ee22-40d1-840a-0dae97e8bf09",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/rna/run_2/run_2_tnscope.output.twist.neoantigen.vep.rna.vcf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/vcf_tnscope_filter_neoantigen.vcf",
            upload_placeholder="78621828-ee22-40d1-840a-0dae97e8bf09",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/germline/CTTTPP111.00/CTTTPP111.00_haplotyper.targets.vcf.gz",
            gs_key="test_prism_trial_id/wes/run_1/analysis/normal/CTTTPP111.00/haplotyper_targets.vcf.gz",
            upload_placeholder="ht899d73-7373-4041-85f9-6cc4324be812",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/germline/CTTTPP111.00/CTTTPP111.00_haplotyper.output.vcf",
            gs_key="test_prism_trial_id/wes/run_1/analysis/normal/CTTTPP111.00/haplotyper_output.vcf",
            upload_placeholder="it899d73-7373-4041-85f9-6cc4324be812",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/hlahd/CTTTPP111.00/result/CTTTPP111.00_final.result.txt",
            gs_key="test_prism_trial_id/wes/run_1/analysis/normal/CTTTPP111.00/hla_final_result.txt",
            upload_placeholder="7b36da9d-c015-42be-80df-d22c17a29124",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/optitype/CTTTPP111.00/CTTTPP111.00_result.tsv",
            gs_key="test_prism_trial_id/wes/run_1/analysis/normal/CTTTPP111.00/optitype_result.tsv",
            upload_placeholder="6b36da9d-c015-42be-80df-d22c17a29124",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/xhla/CTTTPP111.00/report-CTTTPP111.00-hla.json",
            gs_key="test_prism_trial_id/wes/run_1/analysis/normal/CTTTPP111.00/xhla_report_hla.json",
            upload_placeholder="f6a76030-cf27-41e6-8836-17c99479001e",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/run_2_error.yaml",
            gs_key="test_prism_trial_id/wes/run_2/analysis/error.yaml",
            upload_placeholder="a4cba177-0be5-4d7d-b635-4a60adaa9576",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_2/run_2_pyclone6.input.tsv",
            gs_key="test_prism_trial_id/wes/run_2/analysis/clonality_input.tsv",
            upload_placeholder="a4cba177-0be5-4d7d-b635-4a60adaa9575",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_2/run_2_pyclone6.results.tsv",
            gs_key="test_prism_trial_id/wes/run_2/analysis/clonality_results.tsv",
            upload_placeholder="aucba177-0be5-4d7d-b635-4a60adaa9575",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_2/run_2_pyclone6.results.summary.tsv",
            gs_key="test_prism_trial_id/wes/run_2/analysis/clonality_summary.tsv",
            upload_placeholder="b4cba177-0be5-4d7d-b635-4a60adaa9575",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/cnvkit/run_2/run_2.call.cns",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_cnv_segments.cns",
            upload_placeholder="bucba177-0be5-4d7d-b635-4a60adaa9575",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/cnvkit/run_2/run_2.call.enhanced.cns",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_cnv_segments_enhanced.cns",
            upload_placeholder="c4cba177-0be5-4d7d-b635-4a60adaa9575",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/cnvkit/run_2/run_2.scatter.png",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_cnv_scatterplot.png",
            upload_placeholder="cucba177-0be5-4d7d-b635-4a60adaa9575",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/cnvkit/run_2/run_2_cnvkit_gainLoss.bed",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_cnvkit_gainloss.bed",
            upload_placeholder="d4cba177-0be5-4d7d-b635-4a60adaa9575",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_2/run_2_segments.txt",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_segments.txt",
            upload_placeholder="c187bcfe-b454-46a5-bf85-e2a2d5f7a9a5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_2/run_2_genome_view.pdf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_genome_view.pdf",
            upload_placeholder="ba2984c0-f7e6-470c-95ef-e4b33cbdea48",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_2/run_2_chromosome_view.pdf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_chromosome_view.pdf",
            upload_placeholder="d187bcfe-b454-46a5-bf85-e2a2d5f7a9a5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_2/run_2_sequenza_gainLoss.bed",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_sequenza_gainloss.bed",
            upload_placeholder="ca2984c0-f7e6-470c-95ef-e4b33cbdea48",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/clonality/run_2/run_2.bin50.final.seqz.txt.gz",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_sequenza_final.txt.gz",
            upload_placeholder="e187bcfe-b454-46a5-bf85-e2a2d5f7a9a5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/copynumber/run_2/run_2_consensus.bed",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_consensus.bed",
            upload_placeholder="f187bcfe-b454-46a5-bf85-e2a2d5f7a9a5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/copynumber/run_2/run_2_consensus_merged_GAIN.bed",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_consensus_gain.bed",
            upload_placeholder="da2984c0-f7e6-470c-95ef-e4b33cbdea48",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/copynumber/run_2/run_2_consensus_merged_LOSS.bed",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_consensus_loss.bed",
            upload_placeholder="g187bcfe-b454-46a5-bf85-e2a2d5f7a9a5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/purity/run_2/run_2.cncf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_facets.cncf",
            upload_placeholder="ea2984c0-f7e6-470c-95ef-e4b33cbdea48",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/purity/run_2/run_2_facets_gainLoss.bed",
            gs_key="test_prism_trial_id/wes/run_2/analysis/copynumber_facets_gainloss.bed",
            upload_placeholder="h187bcfe-b454-46a5-bf85-e2a2d5f7a9a5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/msisensor2/run_2/run_2_msisensor2.txt",
            gs_key="test_prism_trial_id/wes/run_2/analysis/msisensor.txt",
            upload_placeholder="msi28d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_2/run_2_tnscope.output.twist.vcf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tnscope_output_twist.vcf",
            upload_placeholder="64466c04-86f8-44af-953d-0cfb10d11b34",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_2/run_2_tnscope.output.vcf.gz",
            gs_key="test_prism_trial_id/wes/run_2/analysis/vcf_gz_tnscope_output.vcf.gz",
            upload_placeholder="84466c04-86f8-44af-953d-0cfb10d11b36",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/tcellextrect/run_2/run_2_tcellextrect.txt",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tcellextrect.txt",
            upload_placeholder="1d589bba-708c-449f-879f-44cba199c635",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_2/run_2_tnscope.output.twist.filtered.vcf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tnscope_output_twist_filtered.vcf",
            upload_placeholder="88466c04-86f8-44af-953d-0cfb10d11b88",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_2/run_2_tnscope.output.twist.filtered.maf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tnscope_output_twist_filtered.maf",
            upload_placeholder="773b8502-d7cc-4002-a96d-57e635f4f277",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_2/run_2_tnscope.output.twist.maf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tnscope_output_twist.maf",
            upload_placeholder="66589bba-708c-449f-879f-44cba199c666",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/hlahd/CTTTPP121.00/result/CTTTPP121.00_final.result.txt",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tumor/CTTTPP121.00/hla_final_result.txt",
            upload_placeholder="84f6bd4c-00db-4ce3-a6b6-a8482a3332sg",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/config.yaml",
            gs_key="test_prism_trial_id/wes/run_2/analysis/config.yaml",
            upload_placeholder="abc24763-fb9f-48b4-b7c4-7175759933f5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/metasheet.csv",
            gs_key="test_prism_trial_id/wes/run_2/analysis/metasheet.csv",
            upload_placeholder="xyz271fb-e2c7-5436-cafe-5cf84bc72bf4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report.tar.gz",
            gs_key="test_prism_trial_id/wes/run_2/analysis/report.tar.gz",
            upload_placeholder="yyz271fb-e2c7-5436-cafe-5cf84bc72bf5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/json/run_2.wes.json",
            gs_key="test_prism_trial_id/wes/run_2/analysis/wes_sample.json",
            upload_placeholder="yyz271fb-e2c7-5436-cafe-5cf84bc72bs2",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/WES_Meta/02_WES_Run_Version.tsv",
            gs_key="test_prism_trial_id/wes/run_2/analysis/wes_run_version.tsv",
            upload_placeholder="56824763-fb9f-58b4-c7c4-8175759933f4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/somatic_variants/05_tumor_germline_overlap.tsv",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tumor_germline_overlap.tsv",
            upload_placeholder="66824763-fb9f-58b4-c7c4-8175759933f5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/purity/run_2/run_2.optimalpurityvalue.txt",
            gs_key="test_prism_trial_id/wes/run_2/analysis/optimal_purity_value.txt",
            upload_placeholder="76824763-fb9f-58b4-c7c4-8175759933f6",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/neoantigen/run_2/combined/run_2.filtered.tsv",
            gs_key="test_prism_trial_id/wes/run_2/analysis/combined_filtered.tsv",
            upload_placeholder="86824763-fb9f-58b4-c7c4-8175759933f7",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00.sorted.dedup.bam",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tumor/CTTTPP121.00/sorted.dedup.bam",
            upload_placeholder="d23d0858-eabb-4e9d-ad42-9bb4edadfd59",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00.sorted.dedup.bam.bai",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tumor/CTTTPP121.00/sorted.dedup.bam.bai",
            upload_placeholder="ea9a388b-d679-4a77-845f-2c4073425128",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00_recalibrated.bam",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tumor/CTTTPP121.00/recalibrated.bam",
            upload_placeholder="e23d0858-eabb-4e9d-ad42-9bb4edadfd59",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00_recalibrated.bam.bai",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tumor/CTTTPP121.00/recalibrated.bam.bai",
            upload_placeholder="fa9a388b-d679-4a77-845f-2c4073425128",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/germline/CTTTPP121.00/CTTTPP121.00_haplotyper.output.vcf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tumor/CTTTPP121.00/haplotyper_output.vcf",
            upload_placeholder="it899d73-7373-4041-85f9-6cc4324be813",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/germline/CTTTPP121.00/CTTTPP121.00_haplotyper.targets.vcf.gz",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tumor/CTTTPP121.00/haplotyper_targets.vcf.gz",
            upload_placeholder="ht899d73-7373-4041-85f9-6cc4324be813",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/optitype/CTTTPP121.00/CTTTPP121.00_result.tsv",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tumor/CTTTPP121.00/optitype_result.tsv",
            upload_placeholder="671d710e-f245-4d2b-8732-2774e26aec10",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/xhla/CTTTPP121.00/report-CTTTPP121.00-hla.json",
            gs_key="test_prism_trial_id/wes/run_2/analysis/tumor/CTTTPP121.00/xhla_report_hla.json",
            upload_placeholder="4807aaa5-bafa-4fe5-89e9-73f9d734b971",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00.sorted.dedup.bam",
            gs_key="test_prism_trial_id/wes/run_2/analysis/normal/CTTTPP121.00/sorted.dedup.bam",
            upload_placeholder="f2b13d18-36a2-4273-a69c-a143415231db",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00.sorted.dedup.bam.bai",
            gs_key="test_prism_trial_id/wes/run_2/analysis/normal/CTTTPP121.00/sorted.dedup.bam.bai",
            upload_placeholder="4a06b799-2eb8-47f3-92fa-f5e21da85697",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00_recalibrated.bam",
            gs_key="test_prism_trial_id/wes/run_2/analysis/normal/CTTTPP121.00/recalibrated.bam",
            upload_placeholder="g2b13d18-36a2-4273-a69c-a143415231db",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00_recalibrated.bam.bai",
            gs_key="test_prism_trial_id/wes/run_2/analysis/normal/CTTTPP121.00/recalibrated.bam.bai",
            upload_placeholder="5a06b799-2eb8-47f3-92fa-f5e21da85697",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/germline/CTTTPP121.00/CTTTPP121.00_haplotyper.targets.vcf.gz",
            gs_key="test_prism_trial_id/wes/run_2/analysis/normal/CTTTPP121.00/haplotyper_targets.vcf.gz",
            upload_placeholder="ht899d73-7373-4041-85f9-6cc4324be814",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/germline/CTTTPP121.00/CTTTPP121.00_haplotyper.output.vcf",
            gs_key="test_prism_trial_id/wes/run_2/analysis/normal/CTTTPP121.00/haplotyper_output.vcf",
            upload_placeholder="it899d73-7373-4041-85f9-6cc4324be814",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/hlahd/CTTTPP121.00/result/CTTTPP121.00_final.result.txt",
            gs_key="test_prism_trial_id/wes/run_2/analysis/normal/CTTTPP121.00/hla_final_result.txt",
            upload_placeholder="0371d710-e3d0-4d1b-b87f-23bbadc4ae7e",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/optitype/CTTTPP121.00/CTTTPP121.00_result.tsv",
            gs_key="test_prism_trial_id/wes/run_2/analysis/normal/CTTTPP121.00/optitype_result.tsv",
            upload_placeholder="9371d710-e3d0-4d1b-b87f-23bbadc4ae7e",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/xhla/CTTTPP121.00/report-CTTTPP121.00-hla.json",
            gs_key="test_prism_trial_id/wes/run_2/analysis/normal/CTTTPP121.00/xhla_report_hla.json",
            upload_placeholder="1d0c1f42-6a58-4e4b-b127-208c33f2aeb6",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        sample["cimac_id"]
        for pair_run in prismify_patch["analysis"]["wes_analysis"]["pair_runs"]
        for sample in [pair_run["tumor"], pair_run["normal"]]
    ] + [
        sample["cimac_id"]
        for sample in prismify_patch["analysis"]["wes_analysis"]["excluded_samples"]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "analysis")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@analysis_data_generator
def wes_tumor_only_analysis() -> PrismTestData:
    upload_type = "wes_tumor_only_analysis"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "analysis": {
            "wes_tumor_only_analysis": {
                "runs": [
                    {
                        "run_id": "run_1",
                        "error": {
                            "upload_placeholder": "msi18d7a-fd96-4e75-b265-1590c703a302"
                        },
                        "msisensor": {
                            "msisensor": {
                                "upload_placeholder": "msi18d7a-fd96-4e75-b265-1590c703a301"
                            }
                        },
                        "neoantigen": {
                            "combined_filtered": {
                                "upload_placeholder": "f47271fb-e2c7-5436-cafe-5cf84bc72bf7"
                            },
                        },
                        "somatic": {
                            "vcf_gz_tnscope_output": {
                                "upload_placeholder": "c86ab142-b925-433c-bb13-030c0684365f"
                            },
                            "tnscope_output_twist_vcf": {
                                "upload_placeholder": "64466c04-86f8-44af-953d-0cfb10d11b99"
                            },
                            "tnscope_output_twist_maf": {
                                "upload_placeholder": "1d589bba-708c-449f-879f-44cba199c666"
                            },
                            "tnscope_output_twist_filtered_vcf": {
                                "upload_placeholder": "84466c04-86f8-44af-953d-0cfb10d11b88"
                            },
                            "tnscope_output_twist_filtered_maf": {
                                "upload_placeholder": "e73b8502-d7cc-4002-a96d-57e635f4f277"
                            },
                        },
                        "rna": {
                            "haplotyper": {
                                "upload_placeholder": "e0b85ef8-47cb-45b9-bb94-c961150786b9"
                            },
                            "vcf_tnscope_filter_neoantigen": {
                                "upload_placeholder": "d0b85ef8-47cb-45b9-bb94-c961150786b9"
                            },
                        },
                        "tcell": {
                            "tcellextrect": {
                                "upload_placeholder": "e47271fb-e2c7-5436-cafe-5cf84bc72bf6"
                            }
                        },
                        "tumor": {
                            "cimac_id": "CTTTPP111.00",
                            "alignment": {
                                "align_sorted_dedup": {
                                    "upload_placeholder": "2068ae50-3ce7-4b0c-ba56-f678233dd098"
                                },
                                "align_sorted_dedup_index": {
                                    "upload_placeholder": "cc4ce43e-bc4f-4a93-b482-454f874421a8"
                                },
                                "align_recalibrated": {
                                    "upload_placeholder": "b86ab143-a925-433c-bb13-030c0684365e"
                                },
                                "align_recalibrated_index": {
                                    "upload_placeholder": "54991cf3-b1b9-4b4a-830d-4eade9ef1321"
                                },
                            },
                            "hla": {
                                "hla_final_result": {
                                    "upload_placeholder": "85989077-49e4-44c6-8788-3b19357d3122"
                                },
                                "optitype_result": {
                                    "upload_placeholder": "a5899d73-7373-4041-85f9-6cc4324be817"
                                },
                                "xhla_report_hla": {
                                    "upload_placeholder": "2f3307bd-960e-4735-b831-f93d20fe8d37"
                                },
                            },
                        },
                        "report": {
                            "config": {
                                "upload_placeholder": "abc271fb-d2c7-4436-bafe-4cf84bc72bf4"
                            },
                            "wes_run_version": {
                                "upload_placeholder": "c47271fb-e2c7-5436-cafe-5cf84bc72bf4"
                            },
                            "metasheet": {
                                "upload_placeholder": "xyz271fb-e2c7-5436-cafe-5cf84bc72bf4"
                            },
                            "report": {
                                "upload_placeholder": "yyz271fb-e2c7-5436-cafe-5cf84bc72bf5"
                            },
                            "wes_sample_json": {
                                "upload_placeholder": "yyz24763-fb9f-58b4-c7c4-8175759933s1"
                            },
                        },
                    },
                    {
                        "run_id": "run_2",
                        "error": {
                            "upload_placeholder": "msi28d7a-fd96-4e75-b265-1590c703a302"
                        },
                        "msisensor": {
                            "msisensor": {
                                "upload_placeholder": "msi28d7a-fd96-4e75-b265-1590c703a301"
                            }
                        },
                        "neoantigen": {
                            "combined_filtered": {
                                "upload_placeholder": "86824763-fb9f-58b4-c7c4-8175759933f7"
                            },
                        },
                        "somatic": {
                            "vcf_gz_tnscope_output": {
                                "upload_placeholder": "84466c04-86f8-44af-953d-1cfb10d11b36"
                            },
                            "tnscope_output_twist_vcf": {
                                "upload_placeholder": "64466c04-86f8-44af-953d-0cfb10d11999"
                            },
                            "tnscope_output_twist_maf": {
                                "upload_placeholder": "1d589bba-708c-449f-879f-44cba1996666"
                            },
                            "tnscope_output_twist_filtered_vcf": {
                                "upload_placeholder": "84466c04-86f8-44af-953d-0cfb10d11888"
                            },
                            "tnscope_output_twist_filtered_maf": {
                                "upload_placeholder": "e73b8502-d7cc-4002-a96d-57e635f4f777"
                            },
                        },
                        "tcell": {
                            "tcellextrect": {
                                "upload_placeholder": "64566c04-86f8-44af-953d-0cfb10d11b34"
                            },
                        },
                        "tumor": {
                            "cimac_id": "CTTTPP121.00",
                            "alignment": {
                                "align_sorted_dedup": {
                                    "upload_placeholder": "d23d0858-eabb-4e9d-ad42-9bb4edadfd59"
                                },
                                "align_sorted_dedup_index": {
                                    "upload_placeholder": "ea9a388b-d679-4a77-845f-2c4073425128"
                                },
                                "align_recalibrated": {
                                    "upload_placeholder": "c187bcfe-b454-46a5-bf85-e2a2d5f7a9a5"
                                },
                                "align_recalibrated_index": {
                                    "upload_placeholder": "ba2984c0-f7e6-470c-95ef-e4b33cbdea48"
                                },
                            },
                            "hla": {
                                "hla_final_result": {
                                    "upload_placeholder": "76824763-fb9f-58b4-c7c4-8175759933f6"
                                },
                                "optitype_result": {
                                    "upload_placeholder": "671d710e-f245-4d2b-8732-2774e26aec10"
                                },
                                "xhla_report_hla": {
                                    "upload_placeholder": "4807aaa5-bafa-4fe5-89e9-73f9d734b971"
                                },
                            },
                        },
                        "rna": {
                            "haplotyper": {
                                "upload_placeholder": "88621828-ee22-40d1-840a-0dae97e8bf09"
                            },
                            "vcf_tnscope_filter_neoantigen": {
                                "upload_placeholder": "78621828-ee22-40d1-840a-0dae97e8bf09"
                            },
                        },
                        "report": {
                            "config": {
                                "upload_placeholder": "abc24763-fb9f-48b4-b7c4-7175759933f5"
                            },
                            "wes_run_version": {
                                "upload_placeholder": "56824763-fb9f-58b4-c7c4-8175759933f4"
                            },
                            "metasheet": {
                                "upload_placeholder": "xyz24763-fb9f-58b4-c7c4-8175759933f4"
                            },
                            "report": {
                                "upload_placeholder": "yyz24763-fb9f-58b4-c7c4-8175759933f5"
                            },
                            "wes_sample_json": {
                                "upload_placeholder": "yyz271fb-e2c7-5436-cafe-5cf84bc72bs2"
                            },
                        },
                    },
                ],
                "excluded_samples": [
                    {"cimac_id": "CTTTPP111.00", "reason_excluded": "low coverage"},
                    {"cimac_id": "CTTTPP122.00", "reason_excluded": "module failed"},
                ],
            }
        },
        "protocol_identifier": "test_prism_trial_id",
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="gs://results/analysis/rna/run_1/run_1.haplotyper.rna.vcf.gz",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/haplotyper.vcf.gz",
            upload_placeholder="e0b85ef8-47cb-45b9-bb94-c961150786b9",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/rna/run_1/run_1_tnscope.output.twist.neoantigen.vep.rna.vcf",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/vcf_tnscope_filter_neoantigen.vcf",
            upload_placeholder="d0b85ef8-47cb-45b9-bb94-c961150786b9",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/hlahd/CTTTPP111.00/result/CTTTPP111.00_final.result.txt",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tumor/CTTTPP111.00/hla_final_result.txt",
            upload_placeholder="85989077-49e4-44c6-8788-3b19357d3122",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/run_1_error.yaml",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/error.yaml",
            upload_placeholder="msi18d7a-fd96-4e75-b265-1590c703a302",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/msisensor2/run_1/run_1_msisensor2.txt",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/msisensor.txt",
            upload_placeholder="msi18d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00_recalibrated.bam",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tumor/CTTTPP111.00/recalibrated.bam",
            upload_placeholder="b86ab143-a925-433c-bb13-030c0684365e",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_1/run_1_tnscope.output.vcf.gz",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/vcf_gz_tnscope_output.vcf.gz",
            upload_placeholder="c86ab142-b925-433c-bb13-030c0684365f",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00_recalibrated.bam.bai",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tumor/CTTTPP111.00/recalibrated.bam.bai",
            upload_placeholder="54991cf3-b1b9-4b4a-830d-4eade9ef1321",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_1/run_1_tnscope.output.twist.vcf",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tnscope_output_twist.vcf",
            upload_placeholder="64466c04-86f8-44af-953d-0cfb10d11b99",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_1/run_1_tnscope.output.twist.filtered.vcf",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tnscope_output_twist_filtered.vcf",
            upload_placeholder="84466c04-86f8-44af-953d-0cfb10d11b88",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_1/run_1_tnscope.output.twist.filtered.maf",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tnscope_output_twist_filtered.maf",
            upload_placeholder="e73b8502-d7cc-4002-a96d-57e635f4f277",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_1/run_1_tnscope.output.twist.maf",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tnscope_output_twist.maf",
            upload_placeholder="1d589bba-708c-449f-879f-44cba199c666",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/config.yaml",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/config.yaml",
            upload_placeholder="abc271fb-d2c7-4436-bafe-4cf84bc72bf4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/metasheet.csv",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/metasheet.csv",
            upload_placeholder="xyz24763-fb9f-58b4-c7c4-8175759933f4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report.tar.gz",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/report.tar.gz",
            upload_placeholder="yyz24763-fb9f-58b4-c7c4-8175759933f5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/json/run_1.wes.json",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/wes_sample.json",
            upload_placeholder="yyz24763-fb9f-58b4-c7c4-8175759933s1",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/WES_Meta/02_WES_Run_Version.tsv",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/wes_run_version.tsv",
            upload_placeholder="c47271fb-e2c7-5436-cafe-5cf84bc72bf4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/tcellextrect/run_1/run_1_tcellextrect.txt",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tcellextrect.txt",
            upload_placeholder="e47271fb-e2c7-5436-cafe-5cf84bc72bf6",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/neoantigen/run_1/combined/run_1.filtered.tsv",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/combined_filtered.tsv",
            upload_placeholder="f47271fb-e2c7-5436-cafe-5cf84bc72bf7",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00.sorted.dedup.bam",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tumor/CTTTPP111.00/sorted.dedup.bam",
            upload_placeholder="2068ae50-3ce7-4b0c-ba56-f678233dd098",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP111.00/CTTTPP111.00.sorted.dedup.bam.bai",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tumor/CTTTPP111.00/sorted.dedup.bam.bai",
            upload_placeholder="cc4ce43e-bc4f-4a93-b482-454f874421a8",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/optitype/CTTTPP111.00/CTTTPP111.00_result.tsv",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tumor/CTTTPP111.00/optitype_result.tsv",
            upload_placeholder="a5899d73-7373-4041-85f9-6cc4324be817",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/xhla/CTTTPP111.00/report-CTTTPP111.00-hla.json",
            gs_key="test_prism_trial_id/wes_tumor_only/run_1/analysis/tumor/CTTTPP111.00/xhla_report_hla.json",
            upload_placeholder="2f3307bd-960e-4735-b831-f93d20fe8d37",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/rna/run_2/run_2.haplotyper.rna.vcf.gz",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/haplotyper.vcf.gz",
            upload_placeholder="88621828-ee22-40d1-840a-0dae97e8bf09",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/rna/run_2/run_2_tnscope.output.twist.neoantigen.vep.rna.vcf",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/vcf_tnscope_filter_neoantigen.vcf",
            upload_placeholder="78621828-ee22-40d1-840a-0dae97e8bf09",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00_recalibrated.bam",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tumor/CTTTPP121.00/recalibrated.bam",
            upload_placeholder="c187bcfe-b454-46a5-bf85-e2a2d5f7a9a5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00_recalibrated.bam.bai",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tumor/CTTTPP121.00/recalibrated.bam.bai",
            upload_placeholder="ba2984c0-f7e6-470c-95ef-e4b33cbdea48",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/run_2_error.yaml",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/error.yaml",
            upload_placeholder="msi28d7a-fd96-4e75-b265-1590c703a302",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/msisensor2/run_2/run_2_msisensor2.txt",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/msisensor.txt",
            upload_placeholder="msi28d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/tcellextrect/run_2/run_2_tcellextrect.txt",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tcellextrect.txt",
            upload_placeholder="64566c04-86f8-44af-953d-0cfb10d11b34",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_2/run_2_tnscope.output.vcf.gz",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/vcf_gz_tnscope_output.vcf.gz",
            upload_placeholder="84466c04-86f8-44af-953d-1cfb10d11b36",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_2/run_2_tnscope.output.twist.vcf",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tnscope_output_twist.vcf",
            upload_placeholder="64466c04-86f8-44af-953d-0cfb10d11999",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_2/run_2_tnscope.output.twist.filtered.vcf",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tnscope_output_twist_filtered.vcf",
            upload_placeholder="84466c04-86f8-44af-953d-0cfb10d11888",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_2/run_2_tnscope.output.twist.filtered.maf",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tnscope_output_twist_filtered.maf",
            upload_placeholder="e73b8502-d7cc-4002-a96d-57e635f4f777",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/somatic/run_2/run_2_tnscope.output.twist.maf",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tnscope_output_twist.maf",
            upload_placeholder="1d589bba-708c-449f-879f-44cba1996666",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/config.yaml",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/config.yaml",
            upload_placeholder="abc24763-fb9f-48b4-b7c4-7175759933f5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/metasheet.csv",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/metasheet.csv",
            upload_placeholder="xyz271fb-e2c7-5436-cafe-5cf84bc72bf4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report.tar.gz",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/report.tar.gz",
            upload_placeholder="yyz271fb-e2c7-5436-cafe-5cf84bc72bf5",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/json/run_2.wes.json",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/wes_sample.json",
            upload_placeholder="yyz271fb-e2c7-5436-cafe-5cf84bc72bs2",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/report/WES_Meta/02_WES_Run_Version.tsv",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/wes_run_version.tsv",
            upload_placeholder="56824763-fb9f-58b4-c7c4-8175759933f4",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/hlahd/CTTTPP121.00/result/CTTTPP121.00_final.result.txt",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tumor/CTTTPP121.00/hla_final_result.txt",
            upload_placeholder="76824763-fb9f-58b4-c7c4-8175759933f6",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/neoantigen/run_2/combined/run_2.filtered.tsv",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/combined_filtered.tsv",
            upload_placeholder="86824763-fb9f-58b4-c7c4-8175759933f7",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00.sorted.dedup.bam",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tumor/CTTTPP121.00/sorted.dedup.bam",
            upload_placeholder="d23d0858-eabb-4e9d-ad42-9bb4edadfd59",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/align/CTTTPP121.00/CTTTPP121.00.sorted.dedup.bam.bai",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tumor/CTTTPP121.00/sorted.dedup.bam.bai",
            upload_placeholder="ea9a388b-d679-4a77-845f-2c4073425128",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/optitype/CTTTPP121.00/CTTTPP121.00_result.tsv",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tumor/CTTTPP121.00/optitype_result.tsv",
            upload_placeholder="671d710e-f245-4d2b-8732-2774e26aec10",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="gs://results/analysis/xhla/CTTTPP121.00/report-CTTTPP121.00-hla.json",
            gs_key="test_prism_trial_id/wes_tumor_only/run_2/analysis/tumor/CTTTPP121.00/xhla_report_hla.json",
            upload_placeholder="4807aaa5-bafa-4fe5-89e9-73f9d734b971",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        run["tumor"]["cimac_id"]
        for run in prismify_patch["analysis"]["wes_tumor_only_analysis"]["runs"]
    ] + [
        sample["cimac_id"]
        for sample in prismify_patch["analysis"]["wes_tumor_only_analysis"][
            "excluded_samples"
        ]
    ]
    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "analysis")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@analysis_data_generator
def rna_level1_analysis() -> PrismTestData:
    upload_type = "rna_level1_analysis"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "analysis": {
            "rna_analysis": {
                "level_1": [
                    {
                        "cimac_id": "CTTTPP111.00",
                        "error": {
                            "upload_placeholder": "03030303-0404-0303-0303-CTTTPP111.00"
                        },
                        "star": {
                            "sorted_bam": {
                                "upload_placeholder": "03030303-0303-0303-0303-CTTTPP111.00"
                            },
                            "sorted_bam_index": {
                                "upload_placeholder": "04040404-0404-0404-0404-CTTTPP111.00"
                            },
                            "sorted_bam_stat_txt": {
                                "upload_placeholder": "05050505-0505-0505-0505-CTTTPP111.00"
                            },
                            "transcriptome_bam": {
                                "upload_placeholder": "16161616-1616-1616-1616-CTTTPP111.00"
                            },
                            "chimeric_out_junction": {
                                "upload_placeholder": "16161616-1616-1616-1717-CTTTPP111.00"
                            },
                        },
                        "rseqc": {
                            "read_distrib": {
                                "upload_placeholder": "21212121-2121-2121-2121-CTTTPP111.00"
                            },
                            "tin_score_summary": {
                                "upload_placeholder": "22222222-2222-2222-2222-CTTTPP111.00"
                            },
                            "tin_score": {
                                "upload_placeholder": "23232323-2323-2323-2323-CTTTPP111.00"
                            },
                        },
                        "salmon": {
                            "quant_sf": {
                                "upload_placeholder": "24242424-2424-2424-2424-CTTTPP111.00"
                            },
                            "transcriptome_bam_log": {
                                "upload_placeholder": "25252525-2525-2525-2525-CTTTPP111.00"
                            },
                            "aux_info_ambig_info_tsv": {
                                "upload_placeholder": "26262626-2626-2626-2626-CTTTPP111.00"
                            },
                            "aux_info_expected_bias": {
                                "upload_placeholder": "27272727-2727-2727-2727-CTTTPP111.00"
                            },
                            "aux_info_fld": {
                                "upload_placeholder": "28282828-2828-2828-2828-CTTTPP111.00"
                            },
                            "aux_info_meta_info": {
                                "upload_placeholder": "29292929-2929-2929-2929-CTTTPP111.00"
                            },
                            "aux_info_observed_bias": {
                                "upload_placeholder": "30303030-3030-3030-3030-CTTTPP111.00"
                            },
                            "aux_info_observed_bias_3p": {
                                "upload_placeholder": "31313131-3131-3131-3131-CTTTPP111.00"
                            },
                            "cmd_info": {
                                "upload_placeholder": "32323232-3232-3232-3232-CTTTPP111.00"
                            },
                            "salmon_quant_log": {
                                "upload_placeholder": "33333333-3333-3333-3333-CTTTPP111.00"
                            },
                        },
                        "microbiome": {
                            "sample_report": {
                                "upload_placeholder": "03030303-0303-0303-0000-CTTTPP111.00"
                            }
                        },
                        "trust4": {
                            "trust4_report": {
                                "upload_placeholder": "03030303-0303-0303-9999-CTTTPP111.00"
                            }
                        },
                        "neoantigen": {
                            "genotype": {
                                "upload_placeholder": "55555555-0303-0303-0303-CTTTPP111.00"
                            }
                        },
                        "msisensor": {
                            "msisensor_report": {
                                "upload_placeholder": "55555555-5555-5555-5555-CTTTPP111.00"
                            }
                        },
                        "fusion": {
                            "fusion_predictions": {
                                "upload_placeholder": "55555555-6666-6666-6667-CTTTPP111.00"
                            }
                        },
                    },
                    {
                        "cimac_id": "CTTTPP121.00",
                        "error": {
                            "upload_placeholder": "03030303-0404-0303-0303-CTTTPP121.00"
                        },
                        "star": {
                            "sorted_bam": {
                                "upload_placeholder": "03030303-0303-0303-0303-CTTTPP121.00"
                            },
                            "sorted_bam_index": {
                                "upload_placeholder": "04040404-0404-0404-0404-CTTTPP121.00"
                            },
                            "sorted_bam_stat_txt": {
                                "upload_placeholder": "05050505-0505-0505-0505-CTTTPP121.00"
                            },
                            "transcriptome_bam": {
                                "upload_placeholder": "16161616-1616-1616-1616-CTTTPP121.00"
                            },
                            "chimeric_out_junction": {
                                "upload_placeholder": "16161616-1616-1616-1717-CTTTPP121.00"
                            },
                        },
                        "rseqc": {
                            "read_distrib": {
                                "upload_placeholder": "21212121-2121-2121-2121-CTTTPP121.00"
                            },
                            "tin_score_summary": {
                                "upload_placeholder": "22222222-2222-2222-2222-CTTTPP121.00"
                            },
                            "tin_score": {
                                "upload_placeholder": "23232323-2323-2323-2323-CTTTPP121.00"
                            },
                        },
                        "salmon": {
                            "quant_sf": {
                                "upload_placeholder": "24242424-2424-2424-2424-CTTTPP121.00"
                            },
                            "transcriptome_bam_log": {
                                "upload_placeholder": "25252525-2525-2525-2525-CTTTPP121.00"
                            },
                            "aux_info_ambig_info_tsv": {
                                "upload_placeholder": "26262626-2626-2626-2626-CTTTPP121.00"
                            },
                            "aux_info_expected_bias": {
                                "upload_placeholder": "27272727-2727-2727-2727-CTTTPP121.00"
                            },
                            "aux_info_fld": {
                                "upload_placeholder": "28282828-2828-2828-2828-CTTTPP121.00"
                            },
                            "aux_info_meta_info": {
                                "upload_placeholder": "29292929-2929-2929-2929-CTTTPP121.00"
                            },
                            "aux_info_observed_bias": {
                                "upload_placeholder": "30303030-3030-3030-3030-CTTTPP121.00"
                            },
                            "aux_info_observed_bias_3p": {
                                "upload_placeholder": "31313131-3131-3131-3131-CTTTPP121.00"
                            },
                            "cmd_info": {
                                "upload_placeholder": "32323232-3232-3232-3232-CTTTPP121.00"
                            },
                            "salmon_quant_log": {
                                "upload_placeholder": "33333333-3333-3333-3333-CTTTPP121.00"
                            },
                        },
                        "microbiome": {
                            "sample_report": {
                                "upload_placeholder": "03030303-0303-0303-0000-CTTTPP121.00"
                            }
                        },
                        "trust4": {
                            "trust4_report": {
                                "upload_placeholder": "03030303-0303-0303-9999-CTTTPP121.00"
                            }
                        },
                        "neoantigen": {
                            "genotype": {
                                "upload_placeholder": "55555555-0303-0303-0303-CTTTPP121.00"
                            }
                        },
                        "msisensor": {
                            "msisensor_report": {
                                "upload_placeholder": "55555555-5555-5555-5555-CTTTPP121.00"
                            }
                        },
                        "fusion": {
                            "fusion_predictions": {
                                "upload_placeholder": "55555555-6666-6666-6667-CTTTPP121.00"
                            }
                        },
                    },
                ],
                "excluded_samples": [
                    {"cimac_id": "CTTTPP111.00", "reason_excluded": "low coverage"},
                    {"cimac_id": "CTTTPP122.00", "reason_excluded": "module failed"},
                ],
            }
        },
        "protocol_identifier": "test_prism_trial_id",
    }

    cimac_ids = [
        r["cimac_id"] for r in prismify_patch["analysis"]["rna_analysis"]["level_1"]
    ]

    upload_entries = sum(
        [
            [
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/{cimac_id}_error.yaml",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/error.yaml",
                    upload_placeholder=f"03030303-0404-0303-0303-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=True,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/star/{cimac_id}/{cimac_id}.sorted.bam",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/star/sorted.bam",
                    upload_placeholder=f"03030303-0303-0303-0303-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/star/{cimac_id}/{cimac_id}.sorted.bam.bai",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/star/sorted.bam.bai",
                    upload_placeholder=f"04040404-0404-0404-0404-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/star/{cimac_id}/{cimac_id}.sorted.bam.stat.txt",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/star/sorted.bam.stat.txt",
                    upload_placeholder=f"05050505-0505-0505-0505-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/star/{cimac_id}/{cimac_id}.transcriptome.bam",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/star/transcriptome.bam",
                    upload_placeholder=f"16161616-1616-1616-1616-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/star/{cimac_id}/{cimac_id}.Chimeric.out.junction",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/star/chimeric_out.junction",
                    upload_placeholder=f"16161616-1616-1616-1717-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/rseqc/read_distrib/{cimac_id}/{cimac_id}.txt",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/rseqc/read_distrib.txt",
                    upload_placeholder=f"21212121-2121-2121-2121-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/rseqc/tin_score/{cimac_id}/{cimac_id}.summary.txt",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/rseqc/tin_score.summary.txt",
                    upload_placeholder=f"22222222-2222-2222-2222-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/rseqc/tin_score/{cimac_id}/{cimac_id}.tin_score.txt",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/rseqc/tin_score.txt",
                    upload_placeholder=f"23232323-2323-2323-2323-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/salmon/{cimac_id}/{cimac_id}.quant.sf",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/salmon/quant.sf",
                    upload_placeholder=f"24242424-2424-2424-2424-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/salmon/{cimac_id}/{cimac_id}.transcriptome.bam.log",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/salmon/transcriptome.bam.log",
                    upload_placeholder=f"25252525-2525-2525-2525-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/salmon/{cimac_id}/aux_info/ambig_info.tsv",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/salmon/aux_info_ambig_info.tsv",
                    upload_placeholder=f"26262626-2626-2626-2626-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/salmon/{cimac_id}/aux_info/expected_bias.gz",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/salmon/aux_info_expected_bias.gz",
                    upload_placeholder=f"27272727-2727-2727-2727-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/salmon/{cimac_id}/aux_info/fld.gz",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/salmon/aux_info_fld.gz",
                    upload_placeholder=f"28282828-2828-2828-2828-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/salmon/{cimac_id}/aux_info/meta_info.json",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/salmon/aux_info_meta_info.json",
                    upload_placeholder=f"29292929-2929-2929-2929-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/salmon/{cimac_id}/aux_info/observed_bias.gz",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/salmon/aux_info_observed_bias.gz",
                    upload_placeholder=f"30303030-3030-3030-3030-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/salmon/{cimac_id}/aux_info/observed_bias_3p.gz",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/salmon/aux_info_observed_bias_3p.gz",
                    upload_placeholder=f"31313131-3131-3131-3131-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/salmon/{cimac_id}/cmd_info.json",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/salmon/cmd_info.json",
                    upload_placeholder=f"32323232-3232-3232-3232-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/salmon/{cimac_id}/logs/salmon_quant.log",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/salmon/salmon_quant.log",
                    upload_placeholder=f"33333333-3333-3333-3333-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/microbiome/{cimac_id}/{cimac_id}_addSample_report.txt",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/microbiome/sample_report.txt",
                    upload_placeholder=f"03030303-0303-0303-0000-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/trust4/{cimac_id}/{cimac_id}_report.tsv",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/trust4/trust4_report.tsv",
                    upload_placeholder=f"03030303-0303-0303-9999-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/neoantigen/{cimac_id}/{cimac_id}.genotype.json",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/neoantigen/genotype.json",
                    upload_placeholder=f"55555555-0303-0303-0303-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/msisensor/single/{cimac_id}/{cimac_id}_msisensor.txt",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/msisensor/msisensor_report.txt",
                    upload_placeholder=f"55555555-5555-5555-5555-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/fusion/{cimac_id}/{cimac_id}.fusion_predictions.abridged_addSample.tsv",
                    gs_key=f"test_prism_trial_id/rna/{cimac_id}/analysis/fusion/fusion_predictions.tsv",
                    upload_placeholder=f"55555555-6666-6666-6667-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
            ]
            for cimac_id in cimac_ids
        ],
        [],
    )

    cimac_ids += [
        sample["cimac_id"]
        for sample in prismify_patch["analysis"]["rna_analysis"]["excluded_samples"]
    ]

    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "analysis")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@analysis_data_generator
def atacseq_analysis() -> PrismTestData:
    upload_type = "atacseq_analysis"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "analysis": {
            "atacseq_analysis": [
                {
                    "records": [
                        {
                            "cimac_id": "CTTTPP111.00",
                            "peaks": {
                                "sorted_peaks_bed": {
                                    "upload_placeholder": "03030303-0303-0303-0303-CTTTPP111.00"
                                },
                                "sorted_summits": {
                                    "upload_placeholder": "04040404-0404-0404-0404-CTTTPP111.00"
                                },
                                "sorted_peaks_narrowpeak": {
                                    "upload_placeholder": "05050505-0505-0505-0505-CTTTPP111.00"
                                },
                                "treat_pileup": {
                                    "upload_placeholder": "16161616-1616-1616-1616-CTTTPP111.00"
                                },
                            },
                            "aligned_sorted_bam": {
                                "upload_placeholder": "22222222-2222-2222-2222-CTTTPP111.00"
                            },
                        },
                        {
                            "cimac_id": "CTTTPP121.00",
                            "peaks": {
                                "sorted_peaks_bed": {
                                    "upload_placeholder": "03030303-0303-0303-0303-CTTTPP121.00"
                                },
                                "sorted_summits": {
                                    "upload_placeholder": "04040404-0404-0404-0404-CTTTPP121.00"
                                },
                                "sorted_peaks_narrowpeak": {
                                    "upload_placeholder": "05050505-0505-0505-0505-CTTTPP121.00"
                                },
                                "treat_pileup": {
                                    "upload_placeholder": "16161616-1616-1616-1616-CTTTPP121.00"
                                },
                            },
                            "aligned_sorted_bam": {
                                "upload_placeholder": "22222222-2222-2222-2222-CTTTPP121.00"
                            },
                        },
                    ],
                    "report": {
                        "upload_placeholder": "22222222-2222-2222-2222-41ebcc0a07d9"
                    },
                    "batch_id": "XYZ",
                    "excluded_samples": [
                        {"cimac_id": "CTTTPP111.00", "reason_excluded": "low coverage"},
                        {
                            "cimac_id": "CTTTPP122.00",
                            "reason_excluded": "module failed",
                        },
                    ],
                }
            ]
        },
        "protocol_identifier": "test_prism_trial_id",
    }

    cimac_ids = [
        r["cimac_id"]
        for r in prismify_patch["analysis"]["atacseq_analysis"][0]["records"]
    ]

    upload_entries = sum(
        [
            [
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/peaks/{cimac_id}.rep1/{cimac_id}.rep1_sorted_peaks.bed",
                    gs_key=f"test_prism_trial_id/atacseq/{cimac_id}/analysis/peaks/sorted_peaks.bed",
                    upload_placeholder=f"03030303-0303-0303-0303-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/peaks/{cimac_id}.rep1/{cimac_id}.rep1_sorted_summits.bed",
                    gs_key=f"test_prism_trial_id/atacseq/{cimac_id}/analysis/peaks/sorted_summits.bed",
                    upload_placeholder=f"04040404-0404-0404-0404-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/peaks/{cimac_id}.rep1/{cimac_id}.rep1_sorted_peaks.narrowPeak",
                    gs_key=f"test_prism_trial_id/atacseq/{cimac_id}/analysis/peaks/sorted_peaks.narrowPeak",
                    upload_placeholder=f"05050505-0505-0505-0505-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/peaks/{cimac_id}.rep1/{cimac_id}.rep1_treat_pileup.bw",
                    gs_key=f"test_prism_trial_id/atacseq/{cimac_id}/analysis/peaks/treat_pileup.bw",
                    upload_placeholder=f"16161616-1616-1616-1616-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
                LocalFileUploadEntry(
                    local_path=f"gs://analysis/align/{cimac_id}/{cimac_id}.sorted.bam",
                    gs_key=f"test_prism_trial_id/atacseq/{cimac_id}/analysis/aligned_sorted.bam",
                    upload_placeholder=f"22222222-2222-2222-2222-{cimac_id}",
                    metadata_availability=False,
                    allow_empty=False,
                ),
            ]
            for cimac_id in cimac_ids
        ],
        [
            LocalFileUploadEntry(
                local_path="test_prism_trial_id/atacseq/analysis/XYZ/report.zip",
                gs_key="test_prism_trial_id/atacseq/analysis/XYZ/report.zip",
                upload_placeholder="22222222-2222-2222-2222-41ebcc0a07d9",
                metadata_availability=False,
                allow_empty=False,
            ),
        ],
    )

    cimac_ids += [
        sample["cimac_id"]
        for sample in prismify_patch["analysis"]["atacseq_analysis"][0][
            "excluded_samples"
        ]
    ]

    base_trial = get_test_trial(cimac_ids)

    target_trial = copy_dict_with_branch(base_trial, prismify_patch, "analysis")

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@analysis_data_generator
def cytof_analysis() -> PrismTestData:
    upload_type = "cytof_analysis"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "assays": {
            "cytof": [
                {
                    "records": [
                        {
                            "cimac_id": "CTTTPP111.00",
                            "output_files": {
                                "fcs_file": {
                                    "upload_placeholder": "a5515c79-e5ff-41a8-bd98-c7e746a84d8c"
                                },
                                "assignment": {
                                    "upload_placeholder": "b54fc467-65d9-4cd3-baa7-9ec508ad56eb"
                                },
                                "compartment": {
                                    "upload_placeholder": "1d2be563-3117-4a6a-9ad3-0351cae2b8c0"
                                },
                                "profiling": {
                                    "upload_placeholder": "3c8b9d95-b3c0-459b-84d3-6ee0b5c42b56"
                                },
                                "cell_counts_assignment": {
                                    "upload_placeholder": "3b7f6d8a-811d-4213-8de3-b1fb92432c37"
                                },
                                "cell_counts_compartment": {
                                    "upload_placeholder": "0b0c9744-6065-4c0d-a595-a3db4f3605ec"
                                },
                                "cell_counts_profiling": {
                                    "upload_placeholder": "bd2588f3-b524-45b9-aba4-05d531a12bfe"
                                },
                            },
                        },
                        {
                            "cimac_id": "CTTTPP121.00",
                            "output_files": {
                                "fcs_file": {
                                    "upload_placeholder": "26fb0ada-8860-4a3d-a278-6b04a36291b9"
                                },
                                "assignment": {
                                    "upload_placeholder": "662a59f1-361c-4cc1-8502-5155120b1ec2"
                                },
                                "compartment": {
                                    "upload_placeholder": "dbcb4352-001a-45d4-bbaf-46f1832859f3"
                                },
                                "profiling": {
                                    "upload_placeholder": "cb714f63-2849-4916-9fe8-421331c08759"
                                },
                                "cell_counts_assignment": {
                                    "upload_placeholder": "91cc578a-77f3-4898-84ab-e124f1cf000f"
                                },
                                "cell_counts_compartment": {
                                    "upload_placeholder": "46f88f77-07ec-46b9-9e9f-53532ae96efc"
                                },
                                "cell_counts_profiling": {
                                    "upload_placeholder": "97634d45-5796-4210-80f6-c7f08c8f1e1d"
                                },
                            },
                        },
                    ],
                    "assay_run_id": "test_prism_trial_id_run_1",
                    "batch_id": "XYZ1",
                    "astrolabe_reports": {
                        "upload_placeholder": "5b09c736-0c99-4908-b288-41ebcc0a07d9"
                    },
                    "astrolabe_analysis": {
                        "upload_placeholder": "6abb7949-5400-4e5a-a947-5a1403ca75cb"
                    },
                    "control_files_analysis": {
                        "upload_placeholder": "4abb7949-5400-4e5a-a947-5a1403ca75c4"
                    },
                    "excluded_samples": [
                        {"cimac_id": "CTTTPP111.00", "reason_excluded": "low coverage"},
                        {
                            "cimac_id": "CTTTPP122.00",
                            "reason_excluded": "module failed",
                        },
                    ],
                },
            ]
        },
        "protocol_identifier": "test_prism_trial_id",
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/fcs.fcs",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/source.fcs",
            upload_placeholder="a5515c79-e5ff-41a8-bd98-c7e746a84d8c",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/assignment.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/assignment.csv",
            upload_placeholder="b54fc467-65d9-4cd3-baa7-9ec508ad56eb",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/comp.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/compartment.csv",
            upload_placeholder="1d2be563-3117-4a6a-9ad3-0351cae2b8c0",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/profiling.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/profiling.csv",
            upload_placeholder="3c8b9d95-b3c0-459b-84d3-6ee0b5c42b56",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/cca.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/cell_counts_assignment.csv",
            upload_placeholder="3b7f6d8a-811d-4213-8de3-b1fb92432c37",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/ccc.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/cell_counts_compartment.csv",
            upload_placeholder="0b0c9744-6065-4c0d-a595-a3db4f3605ec",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/ccp.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/cell_counts_profiling.csv",
            upload_placeholder="bd2588f3-b524-45b9-aba4-05d531a12bfe",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/fcs.fcs",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/source.fcs",
            upload_placeholder="26fb0ada-8860-4a3d-a278-6b04a36291b9",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/assignment.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/assignment.csv",
            upload_placeholder="662a59f1-361c-4cc1-8502-5155120b1ec2",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/comp.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/compartment.csv",
            upload_placeholder="dbcb4352-001a-45d4-bbaf-46f1832859f3",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/profiling.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/profiling.csv",
            upload_placeholder="cb714f63-2849-4916-9fe8-421331c08759",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/cca.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/cell_counts_assignment.csv",
            upload_placeholder="91cc578a-77f3-4898-84ab-e124f1cf000f",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/ccc.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/cell_counts_compartment.csv",
            upload_placeholder="46f88f77-07ec-46b9-9e9f-53532ae96efc",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/ccp.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/cell_counts_profiling.csv",
            upload_placeholder="97634d45-5796-4210-80f6-c7f08c8f1e1d",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="batch1/reports.zip",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/reports.zip",
            upload_placeholder="5b09c736-0c99-4908-b288-41ebcc0a07d9",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="batch1/analysis.zip",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/analysis.zip",
            upload_placeholder="6abb7949-5400-4e5a-a947-5a1403ca75cb",
            metadata_availability=False,
            allow_empty=False,
        ),
        LocalFileUploadEntry(
            local_path="batch1/control_files_analysis.zip",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/control_files_analysis.zip",
            upload_placeholder="4abb7949-5400-4e5a-a947-5a1403ca75c4",
            metadata_availability=False,
            allow_empty=True,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["cytof"]
        for record in [*batch["records"], *batch["excluded_samples"]]
    ]
    assays = cytof().prismify_patch["assays"]
    base_trial = get_test_trial(cimac_ids, assays)

    # Set up the CyTOF target trial to include both assay and analysis metadata
    target_trial = deepcopy(base_trial)
    assay_batches = assays["cytof"]
    analysis_batches = prismify_patch["assays"]["cytof"]
    combined_batches = []
    for assay_batch, analysis_batch in zip(assay_batches, analysis_batches):
        assay_records = assay_batch["records"]
        analysis_records = analysis_batch["records"]
        combined_records = [
            copy_dict_with_branch(assay_record, analysis_record, "output_files")
            for assay_record, analysis_record in zip(assay_records, analysis_records)
        ]
        combined_batch = {**assay_batch, **analysis_batch, "records": combined_records}
        combined_batches.append(combined_batch)

    target_trial = copy_dict_with_branch(
        base_trial, {"assays": {"cytof": combined_batches}}, "assays"
    )

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


@analysis_data_generator
def tcr_analysis() -> PrismTestData:
    upload_type = "tcr_analysis"
    prismify_args = get_prismify_args(upload_type)
    prismify_patch = {
        "protocol_identifier": "test_prism_trial_id",
        "analysis": {
            "tcr_analysis": {
                "batches": [
                    {
                        "batch_id": "XYZ",
                        "summary_info": {
                            "upload_placeholder": "872f4bae-bca8-42f6-a3b7-cb4db27b2e24"
                        },
                        "report_trial": {
                            "upload_placeholder": "912f4bae-bca8-42f6-a3b7-cb4db27b2e24"
                        },
                        "records": [
                            {
                                "cimac_id": "CTTTPP111.00",
                                "tra_clone": {
                                    "upload_placeholder": "0b9a11cb-dcf9-45c3-b276-a4f05c687a80"
                                },
                                "trb_clone": {
                                    "upload_placeholder": "5ddbbe19-e695-4ab4-b02c-9ff98509e202"
                                },
                            },
                            {
                                "cimac_id": "CTTTPP121.00",
                                "tra_clone": {
                                    "upload_placeholder": "3f79f985-eca2-46c4-9148-820144a9d31a"
                                },
                                "trb_clone": {
                                    "upload_placeholder": "92b14796-d52c-4c77-92c5-cf3c0a59ce29"
                                },
                            },
                        ],
                        "excluded_samples": [
                            {
                                "cimac_id": "CTTTPP111.00",
                                "reason_excluded": "low coverage",
                            },
                            {
                                "cimac_id": "CTTTPP122.00",
                                "reason_excluded": "module failed",
                            },
                        ],
                    }
                ],
            }
        },
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="1A_10_0_TRA_clones_umi_count.csv",
            gs_key="test_prism_trial_id/tcr_analysis/XYZ/CTTTPP111.00/tra_clone.csv",
            upload_placeholder="0b9a11cb-dcf9-45c3-b276-a4f05c687a80",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="1A_10_0_TRB_clones_umi_count.csv",
            gs_key="test_prism_trial_id/tcr_analysis/XYZ/CTTTPP111.00/trb_clone.csv",
            upload_placeholder="5ddbbe19-e695-4ab4-b02c-9ff98509e202",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="2A_10_0_TRA_clones_umi_count.csv",
            gs_key="test_prism_trial_id/tcr_analysis/XYZ/CTTTPP121.00/tra_clone.csv",
            upload_placeholder="3f79f985-eca2-46c4-9148-820144a9d31a",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="2A_10_0_TRB_clones_umi_count.csv",
            gs_key="test_prism_trial_id/tcr_analysis/XYZ/CTTTPP121.00/trb_clone.csv",
            upload_placeholder="92b14796-d52c-4c77-92c5-cf3c0a59ce29",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="summary_info.csv",
            gs_key="test_prism_trial_id/tcr_analysis/XYZ/summary_info.csv",
            upload_placeholder="872f4bae-bca8-42f6-a3b7-cb4db27b2e24",
            metadata_availability=False,
            allow_empty=True,
        ),
        LocalFileUploadEntry(
            local_path="9204_report.tar.gz",
            gs_key="test_prism_trial_id/tcr_analysis/XYZ/report_trial.tar.gz",
            upload_placeholder="912f4bae-bca8-42f6-a3b7-cb4db27b2e24",
            metadata_availability=False,
            allow_empty=False,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["analysis"]["tcr_analysis"]["batches"]
        for record in [*batch["records"], *batch["excluded_samples"]]
    ]
    assays = tcr_fastq().prismify_patch["assays"]
    base_trial = get_test_trial(cimac_ids, assays)

    # Set up the TCR target trial to include both assay and analysis metadata
    target_trial = copy_dict_with_branch(
        base_trial,
        {"assays": assays, "analysis": prismify_patch["analysis"]},
        ["assays", "analysis"],
    )

    return PrismTestData(
        upload_type,
        prismify_args,
        prismify_patch,
        upload_entries,
        base_trial,
        target_trial,
    )


missing = set(SUPPORTED_ANALYSES).difference(
    [f.__name__ for f in analysis_data_generators]
)
assert not missing, f"Missing analysis test data generators for {missing}"
