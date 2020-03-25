from copy import deepcopy

from cidc_schemas.prism import SUPPORTED_ANALYSES

from .assay_data import cytof
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
                        "germline": {
                            "vcf_compare": {
                                "upload_placeholder": "9986de8e-84eb-49ba-9270-ca9d6aa0edf0"
                            }
                        },
                        "purity": {
                            "optimal_purity_value": {
                                "upload_placeholder": "f0b85ef8-47cb-45b9-bb94-c961150786b9"
                            }
                        },
                        "clonality": {
                            "clonality_pyclone": {
                                "upload_placeholder": "cdef9e1e-8e04-46ed-a9e6-bb618188a6d6"
                            }
                        },
                        "copynumber": {
                            "copynumber_cnv_calls": {
                                "upload_placeholder": "85989077-49e4-44c6-8788-3b19357d3122"
                            },
                            "copynumber_cnv_calls_tsv": {
                                "upload_placeholder": "eb1a8d7a-fd96-4e75-b265-1590c703a301"
                            },
                        },
                        "neoantigen": {
                            "mhc_class_I_epitopes": {
                                "upload_placeholder": "b02ea27d-66a5-4381-bd8c-3f3e19f7ac10"
                            },
                            "mhc_class_I_filtered_condensed_ranked": {
                                "upload_placeholder": "f62b3afe-7380-4bc6-87a1-5a3181497f42"
                            },
                        },
                        "somatic": {
                            "vcf_tnscope_output": {
                                "upload_placeholder": "1a5993b7-3d93-43cf-ba64-0d260dad3cdd"
                            },
                            "maf_tnscope_output": {
                                "upload_placeholder": "a0a4a694-c0bc-4661-b9be-0b6dff20a240"
                            },
                            "vcf_tnscope_filter": {
                                "upload_placeholder": "a86ab142-a925-433c-bb13-030c0684365d"
                            },
                            "maf_tnscope_filter": {
                                "upload_placeholder": "53991cf3-b1b9-4b4a-830d-4eade9ef1321"
                            },
                            "tnscope_exons_broad": {
                                "upload_placeholder": "09bb7dd5-083e-468e-b5c7-3c8eb3e77a94"
                            },
                            "tnscope_exons_mda": {
                                "upload_placeholder": "e31166e8-9ee3-46b6-abf8-bf2b5d933b68"
                            },
                            "tnscope_exons_mocha": {
                                "upload_placeholder": "218be905-220d-417f-8395-0de84fcd8f1d"
                            },
                        },
                        "corealignments": {
                            "tn_corealigned": {
                                "upload_placeholder": "106abc8b-c2c5-4d2a-8663-5e4b9e1188c4"
                            },
                            "tn_corealigned_index": {
                                "upload_placeholder": "a929e845-4ef6-4c06-bfce-8139780469ed"
                            },
                        },
                        "tumor": {
                            "metrics": {
                                "all_summaries": {
                                    "upload_placeholder": "81613653-16a7-4f6c-b8ff-e916013b61a2"
                                },
                                "coverage_metrics": {
                                    "upload_placeholder": "1ac21de4-6b15-48c0-9a0a-d66b9d99cd49"
                                },
                                "target_metrics": {
                                    "upload_placeholder": "2bdcbe60-09d5-4f98-a1fc-01c374c147f5"
                                },
                                "coverage_metrics_summary": {
                                    "upload_placeholder": "653bd098-3997-494b-8db9-03d114b3fbb3"
                                },
                                "target_metrics_summary": {
                                    "upload_placeholder": "0c0f2c9d-8f75-4b04-8a21-c97b4110de79"
                                },
                                "mosdepth_region_dist_broad": {
                                    "upload_placeholder": "82dc827e-e35a-4a72-b6f9-8d870c87a453"
                                },
                                "mosdepth_region_dist_mda": {
                                    "upload_placeholder": "28bbbff2-c67e-4ac1-b536-624f4e74dde8"
                                },
                                "mosdepth_region_dist_mocha": {
                                    "upload_placeholder": "edaa1d9a-320b-4a66-99a8-84ed62f374be"
                                },
                            },
                            "cimac_id": "CTTTPP111.00",
                            "alignment": {
                                "align_recalibrated": {
                                    "upload_placeholder": "1867f161-78ba-4b6e-a318-c87967114e5e"
                                },
                                "align_recalibrated_index": {
                                    "upload_placeholder": "5639a6c2-81b1-46c3-bc07-614650d15c77"
                                },
                                "align_sorted_dedup": {
                                    "upload_placeholder": "2068ae50-3ce7-4b0c-ba56-f678233dd098"
                                },
                                "align_sorted_dedup_index": {
                                    "upload_placeholder": "cc4ce43e-bc4f-4a93-b482-454f874421a8"
                                },
                            },
                            "optitype": {
                                "optitype_result": {
                                    "upload_placeholder": "a5899d73-7373-4041-85f9-6cc4324be817"
                                },
                                "xhla_report_hla": {
                                    "upload_placeholder": "2f3307bd-960e-4735-b831-f93d20fe8d37"
                                },
                            },
                        },
                        "report": {
                            "wes_version": {
                                "upload_placeholder": "b47271fb-d2c7-4436-bafe-4cf84bc72bf4"
                            }
                        },
                        "normal": {
                            "cimac_id": "CTTTPP111.00",
                            "alignment": {
                                "align_recalibrated": {
                                    "upload_placeholder": "c4a6b91b-7ff2-4fe2-b717-1df35eb78c27"
                                },
                                "align_recalibrated_index": {
                                    "upload_placeholder": "f09b7e12-5be4-420c-821a-81866de03402"
                                },
                                "align_sorted_dedup": {
                                    "upload_placeholder": "c163f7aa-43ba-40f4-b11d-bddb79b41763"
                                },
                                "align_sorted_dedup_index": {
                                    "upload_placeholder": "be406c27-2ef4-477c-93e5-684fbe4f9307"
                                },
                            },
                            "metrics": {
                                "coverage_metrics": {
                                    "upload_placeholder": "907d981b-7ca9-4bb9-a10f-ab4aa808c5a3"
                                },
                                "target_metrics": {
                                    "upload_placeholder": "29b2cc56-422c-478c-8c6d-ee040ca1e6df"
                                },
                                "coverage_metrics_summary": {
                                    "upload_placeholder": "3b5fded9-7274-45a4-a71e-48cf590814a9"
                                },
                                "target_metrics_summary": {
                                    "upload_placeholder": "d99b7fed-0501-4177-85e5-a0a57b051eff"
                                },
                                "mosdepth_region_dist_broad": {
                                    "upload_placeholder": "f63b5f01-a2fa-403d-a7c0-4561dadfbedd"
                                },
                                "mosdepth_region_dist_mda": {
                                    "upload_placeholder": "041dc89f-e374-4808-82a6-9a63caa98f65"
                                },
                                "mosdepth_region_dist_mocha": {
                                    "upload_placeholder": "55776c65-0e65-4063-97f5-500ceb65d0f2"
                                },
                            },
                            "optitype": {
                                "optitype_result": {
                                    "upload_placeholder": "6b36da9d-c015-42be-80df-d22c17a29124"
                                },
                                "xhla_report_hla": {
                                    "upload_placeholder": "f6a76030-cf27-41e6-8836-17c99479001e"
                                },
                            },
                        },
                    },
                    {
                        "run_id": "run_2",
                        "germline": {
                            "vcf_compare": {
                                "upload_placeholder": "45f1f7d1-4a48-48d5-9ee3-e7ccc4474d25"
                            }
                        },
                        "purity": {
                            "optimal_purity_value": {
                                "upload_placeholder": "98621828-ee22-40d1-840a-0dae97e8bf09"
                            }
                        },
                        "clonality": {
                            "clonality_pyclone": {
                                "upload_placeholder": "a4cba177-0be5-4d7d-b635-4a60adaa9575"
                            }
                        },
                        "copynumber": {
                            "copynumber_cnv_calls": {
                                "upload_placeholder": "c187bcfe-b454-46a5-bf85-e2a2d5f7a9a5"
                            },
                            "copynumber_cnv_calls_tsv": {
                                "upload_placeholder": "ba2984c0-f7e6-470c-95ef-e4b33cbdea48"
                            },
                        },
                        "neoantigen": {
                            "mhc_class_I_epitopes": {
                                "upload_placeholder": "fe544ce8-d891-400f-8680-f241d0d7cddc"
                            },
                            "mhc_class_I_filtered_condensed_ranked": {
                                "upload_placeholder": "032d8195-cde7-484f-aa56-25f950eeb1ad"
                            },
                        },
                        "somatic": {
                            "vcf_tnscope_output": {
                                "upload_placeholder": "478bb88c-ab41-4423-87d9-6e49ada70b96"
                            },
                            "maf_tnscope_output": {
                                "upload_placeholder": "e73b8502-d7cc-4002-a96d-57e635f4f2b0"
                            },
                            "vcf_tnscope_filter": {
                                "upload_placeholder": "54466c04-86f8-44af-953d-0cfb10d11b33"
                            },
                            "maf_tnscope_filter": {
                                "upload_placeholder": "1d589bba-708c-449f-879f-44cba199c635"
                            },
                            "tnscope_exons_broad": {
                                "upload_placeholder": "ba9d4b22-5610-4cde-b7e1-31ebf856a4ab"
                            },
                            "tnscope_exons_mda": {
                                "upload_placeholder": "267e4b9f-e4b6-464a-bafb-44c0e405e44e"
                            },
                            "tnscope_exons_mocha": {
                                "upload_placeholder": "84f6bd4c-00db-4ce3-a6b6-a8482a333b25"
                            },
                        },
                        "corealignments": {
                            "tn_corealigned": {
                                "upload_placeholder": "9bad3bcb-1b37-4564-bd05-1a919b320f1b"
                            },
                            "tn_corealigned_index": {
                                "upload_placeholder": "4667eb84-13dd-4143-81f5-2e7272441daf"
                            },
                        },
                        "tumor": {
                            "metrics": {
                                "all_summaries": {
                                    "upload_placeholder": "5dfc766a-d447-4279-abc4-3b93890b1e41"
                                },
                                "coverage_metrics": {
                                    "upload_placeholder": "bc055607-9085-4f47-91e5-8f412c4dfafd"
                                },
                                "target_metrics": {
                                    "upload_placeholder": "95e70b6a-1ddc-4bfe-84eb-6c4a6f1ee35d"
                                },
                                "coverage_metrics_summary": {
                                    "upload_placeholder": "3db263fd-2b23-4905-8389-dc8c49c01c2f"
                                },
                                "target_metrics_summary": {
                                    "upload_placeholder": "3dd1b2c5-d5bd-44cc-b994-32cba3cab5d4"
                                },
                                "mosdepth_region_dist_broad": {
                                    "upload_placeholder": "3c5664be-f99a-406d-8849-8064d41a92fe"
                                },
                                "mosdepth_region_dist_mda": {
                                    "upload_placeholder": "a19d90c6-4794-4628-b1c8-dd603b7f6ff1"
                                },
                                "mosdepth_region_dist_mocha": {
                                    "upload_placeholder": "2b3fbb1a-8182-4409-a90e-c69ee75cb194"
                                },
                            },
                            "cimac_id": "CTTTPP121.00",
                            "alignment": {
                                "align_recalibrated": {
                                    "upload_placeholder": "8d800118-9066-414f-a869-8d6574bdb803"
                                },
                                "align_recalibrated_index": {
                                    "upload_placeholder": "47a180b1-8ce7-4268-ba8e-cc470610c812"
                                },
                                "align_sorted_dedup": {
                                    "upload_placeholder": "d23d0858-eabb-4e9d-ad42-9bb4edadfd59"
                                },
                                "align_sorted_dedup_index": {
                                    "upload_placeholder": "ea9a388b-d679-4a77-845f-2c4073425128"
                                },
                            },
                            "optitype": {
                                "optitype_result": {
                                    "upload_placeholder": "671d710e-f245-4d2b-8732-2774e26aec10"
                                },
                                "xhla_report_hla": {
                                    "upload_placeholder": "4807aaa5-bafa-4fe5-89e9-73f9d734b971"
                                },
                            },
                        },
                        "report": {
                            "wes_version": {
                                "upload_placeholder": "46824763-fb9f-48b4-b7c4-7175759933f4"
                            }
                        },
                        "normal": {
                            "cimac_id": "CTTTPP121.00",
                            "alignment": {
                                "align_recalibrated": {
                                    "upload_placeholder": "d7ef5d2c-f2e8-469c-8666-c246ad74cf8b"
                                },
                                "align_recalibrated_index": {
                                    "upload_placeholder": "1120d6c5-ee45-4612-a6e8-2f345ec2a719"
                                },
                                "align_sorted_dedup": {
                                    "upload_placeholder": "f2b13d18-36a2-4273-a69c-a143415231db"
                                },
                                "align_sorted_dedup_index": {
                                    "upload_placeholder": "4a06b799-2eb8-47f3-92fa-f5e21da85697"
                                },
                            },
                            "metrics": {
                                "coverage_metrics": {
                                    "upload_placeholder": "5566abb7-6bfb-4a0f-94a3-f3b02979a131"
                                },
                                "target_metrics": {
                                    "upload_placeholder": "d92c402a-d9a5-4e6c-998d-b56b1b0b7ffa"
                                },
                                "coverage_metrics_summary": {
                                    "upload_placeholder": "de83d3c9-6b0d-4317-b01e-dd28183744f7"
                                },
                                "target_metrics_summary": {
                                    "upload_placeholder": "cd4af4a4-da0d-4af9-b443-b5c15f85189b"
                                },
                                "mosdepth_region_dist_broad": {
                                    "upload_placeholder": "1ffc81e4-0b97-437d-85a8-9389b59727b5"
                                },
                                "mosdepth_region_dist_mda": {
                                    "upload_placeholder": "15933a57-70bf-4db0-b227-ab9ff5ce6258"
                                },
                                "mosdepth_region_dist_mocha": {
                                    "upload_placeholder": "c92dde2b-bf94-4b85-8185-2cf19fd5b7ee"
                                },
                            },
                            "optitype": {
                                "optitype_result": {
                                    "upload_placeholder": "9371d710-e3d0-4d1b-b87f-23bbadc4ae7e"
                                },
                                "xhla_report_hla": {
                                    "upload_placeholder": "1d0c1f42-6a58-4e4b-b127-208c33f2aeb6"
                                },
                            },
                        },
                    },
                ]
            }
        },
        "protocol_identifier": "test_prism_trial_id",
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="analysis/germline/run_1/run_1_vcfcompare.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/vcfcompare.txt",
            upload_placeholder="9986de8e-84eb-49ba-9270-ca9d6aa0edf0",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/purity/run_1/run_1.optimalpurityvalue.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/optimalpurityvalue.txt",
            upload_placeholder="f0b85ef8-47cb-45b9-bb94-c961150786b9",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/clonality/run_1/run_1_pyclone.tsv",
            gs_key="test_prism_trial_id/run_1/wes_analysis/clonality_pyclone.tsv",
            upload_placeholder="cdef9e1e-8e04-46ed-a9e6-bb618188a6d6",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/copynumber/run_1/run_1_cnvcalls.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/copynumber_cnvcalls.txt",
            upload_placeholder="85989077-49e4-44c6-8788-3b19357d3122",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/copynumber/run_1/run_1_cnvcalls.txt.tn.tsv",
            gs_key="test_prism_trial_id/run_1/wes_analysis/copynumber_cnvcalls.txt.tn.tsv",
            upload_placeholder="eb1a8d7a-fd96-4e75-b265-1590c703a301",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/neoantigen/run_1/MHC_Class_I/run_1.all_epitopes.tsv",
            gs_key="test_prism_trial_id/run_1/wes_analysis/MHC_Class_I_all_epitopes.tsv",
            upload_placeholder="b02ea27d-66a5-4381-bd8c-3f3e19f7ac10",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/neoantigen/run_1/MHC_Class_I/run_1.filtered.condensed.ranked.tsv",
            gs_key="test_prism_trial_id/run_1/wes_analysis/MHC_Class_I_filtered_condensed_ranked.tsv",
            upload_placeholder="f62b3afe-7380-4bc6-87a1-5a3181497f42",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_1/run_1_tnscope.output.vcf",
            gs_key="test_prism_trial_id/run_1/wes_analysis/vcf_tnscope_output.vcf",
            upload_placeholder="1a5993b7-3d93-43cf-ba64-0d260dad3cdd",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_1/run_1_tnscope.output.maf",
            gs_key="test_prism_trial_id/run_1/wes_analysis/maf_tnscope_output.maf",
            upload_placeholder="a0a4a694-c0bc-4661-b9be-0b6dff20a240",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_1/run_1_tnscope.filter.vcf",
            gs_key="test_prism_trial_id/run_1/wes_analysis/vcf_tnscope_filter.vcf",
            upload_placeholder="a86ab142-a925-433c-bb13-030c0684365d",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_1/run_1_tnscope.filter.maf",
            gs_key="test_prism_trial_id/run_1/wes_analysis/maf_tnscope_filter.maf",
            upload_placeholder="53991cf3-b1b9-4b4a-830d-4eade9ef1321",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_1/run_1_tnscope.filter.exons.broad.vcf.gz",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tnscope_exons_broad.gz",
            upload_placeholder="09bb7dd5-083e-468e-b5c7-3c8eb3e77a94",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_1/run_1_tnscope.filter.exons.mda.vcf.gz",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tnscope_exons_mda.gz",
            upload_placeholder="e31166e8-9ee3-46b6-abf8-bf2b5d933b68",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_1/run_1_tnscope.filter.exons.mocha.vcf.gz",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tnscope_exons_mocha.gz",
            upload_placeholder="218be905-220d-417f-8395-0de84fcd8f1d",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/corealignments/run_1/run_1_tn_corealigned.bam",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tn_corealigned.bam",
            upload_placeholder="106abc8b-c2c5-4d2a-8663-5e4b9e1188c4",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/corealignments/run_1/run_1_tn_corealigned.bam.bai",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tn_corealigned.bam.bai",
            upload_placeholder="a929e845-4ef6-4c06-bfce-8139780469ed",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/all_sample_summaries.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/all_summaries.txt",
            upload_placeholder="81613653-16a7-4f6c-b8ff-e916013b61a2",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/report/wes_version.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/wes_version.txt",
            upload_placeholder="b47271fb-d2c7-4436-bafe-4cf84bc72bf4",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP111.00/CTTTPP111.00_recalibrated.bam",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/recalibrated.bam",
            upload_placeholder="1867f161-78ba-4b6e-a318-c87967114e5e",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP111.00/CTTTPP111.00_recalibrated.bam.bai",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/recalibrated.bam.bai",
            upload_placeholder="5639a6c2-81b1-46c3-bc07-614650d15c77",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP111.00/CTTTPP111.00.sorted.dedup.bam",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/sorted.dedup.bam",
            upload_placeholder="2068ae50-3ce7-4b0c-ba56-f678233dd098",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP111.00/CTTTPP111.00.sorted.dedup.bam.bai",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/sorted.dedup.bam.bai",
            upload_placeholder="cc4ce43e-bc4f-4a93-b482-454f874421a8",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00_coverage_metrics.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/coverage_metrics.txt",
            upload_placeholder="1ac21de4-6b15-48c0-9a0a-d66b9d99cd49",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00_target_metrics.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/target_metrics.txt",
            upload_placeholder="2bdcbe60-09d5-4f98-a1fc-01c374c147f5",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00_coverage_metrics.sample_summary.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/coverage_metrics_summary.txt",
            upload_placeholder="653bd098-3997-494b-8db9-03d114b3fbb3",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00_target_metrics.txt.sample_summary.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/target_metrics_summary.txt",
            upload_placeholder="0c0f2c9d-8f75-4b04-8a21-c97b4110de79",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00.broad.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/mosdepth_region_dist_broad.txt",
            upload_placeholder="82dc827e-e35a-4a72-b6f9-8d870c87a453",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00.mda.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/mosdepth_region_dist_mda.txt",
            upload_placeholder="28bbbff2-c67e-4ac1-b536-624f4e74dde8",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00.mocha.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/mosdepth_region_dist_mocha.txt",
            upload_placeholder="edaa1d9a-320b-4a66-99a8-84ed62f374be",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/optitype/CTTTPP111.00/CTTTPP111.00_result.tsv",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/optitype_result.tsv",
            upload_placeholder="a5899d73-7373-4041-85f9-6cc4324be817",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/xhla/CTTTPP111.00/CTTTPP111.00_report-CTTTPP111.00-hla.json",
            gs_key="test_prism_trial_id/run_1/wes_analysis/tumor/CTTTPP111.00/xhla_report_hla.json",
            upload_placeholder="2f3307bd-960e-4735-b831-f93d20fe8d37",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP111.00/CTTTPP111.00_recalibrated.bam",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/recalibrated.bam",
            upload_placeholder="c4a6b91b-7ff2-4fe2-b717-1df35eb78c27",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP111.00/CTTTPP111.00_recalibrated.bam.bai",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/recalibrated.bam.bai",
            upload_placeholder="f09b7e12-5be4-420c-821a-81866de03402",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP111.00/CTTTPP111.00.sorted.dedup.bam",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/sorted.dedup.bam",
            upload_placeholder="c163f7aa-43ba-40f4-b11d-bddb79b41763",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP111.00/CTTTPP111.00.sorted.dedup.bam.bai",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/sorted.dedup.bam.bai",
            upload_placeholder="be406c27-2ef4-477c-93e5-684fbe4f9307",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00_coverage_metrics.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/coverage_metrics.txt",
            upload_placeholder="907d981b-7ca9-4bb9-a10f-ab4aa808c5a3",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00_target_metrics.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/target_metrics.txt",
            upload_placeholder="29b2cc56-422c-478c-8c6d-ee040ca1e6df",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00_coverage_metrics.sample_summary.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/coverage_metrics_summary.txt",
            upload_placeholder="3b5fded9-7274-45a4-a71e-48cf590814a9",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00_target_metrics.txt.sample_summary.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/target_metrics_summary.txt",
            upload_placeholder="d99b7fed-0501-4177-85e5-a0a57b051eff",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00.broad.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/mosdepth_region_dist_broad.txt",
            upload_placeholder="f63b5f01-a2fa-403d-a7c0-4561dadfbedd",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00.mda.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/mosdepth_region_dist_mda.txt",
            upload_placeholder="041dc89f-e374-4808-82a6-9a63caa98f65",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP111.00/CTTTPP111.00.mocha.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/mosdepth_region_dist_mocha.txt",
            upload_placeholder="55776c65-0e65-4063-97f5-500ceb65d0f2",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/optitype/CTTTPP111.00/CTTTPP111.00_result.tsv",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/optitype_result.tsv",
            upload_placeholder="6b36da9d-c015-42be-80df-d22c17a29124",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/xhla/CTTTPP111.00/CTTTPP111.00_report-CTTTPP111.00-hla.json",
            gs_key="test_prism_trial_id/run_1/wes_analysis/normal/CTTTPP111.00/xhla_report_hla.json",
            upload_placeholder="f6a76030-cf27-41e6-8836-17c99479001e",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/germline/run_2/run_2_vcfcompare.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/vcfcompare.txt",
            upload_placeholder="45f1f7d1-4a48-48d5-9ee3-e7ccc4474d25",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/purity/run_2/run_2.optimalpurityvalue.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/optimalpurityvalue.txt",
            upload_placeholder="98621828-ee22-40d1-840a-0dae97e8bf09",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/clonality/run_2/run_2_pyclone.tsv",
            gs_key="test_prism_trial_id/run_2/wes_analysis/clonality_pyclone.tsv",
            upload_placeholder="a4cba177-0be5-4d7d-b635-4a60adaa9575",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/copynumber/run_2/run_2_cnvcalls.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/copynumber_cnvcalls.txt",
            upload_placeholder="c187bcfe-b454-46a5-bf85-e2a2d5f7a9a5",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/copynumber/run_2/run_2_cnvcalls.txt.tn.tsv",
            gs_key="test_prism_trial_id/run_2/wes_analysis/copynumber_cnvcalls.txt.tn.tsv",
            upload_placeholder="ba2984c0-f7e6-470c-95ef-e4b33cbdea48",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/neoantigen/run_2/MHC_Class_I/run_2.all_epitopes.tsv",
            gs_key="test_prism_trial_id/run_2/wes_analysis/MHC_Class_I_all_epitopes.tsv",
            upload_placeholder="fe544ce8-d891-400f-8680-f241d0d7cddc",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/neoantigen/run_2/MHC_Class_I/run_2.filtered.condensed.ranked.tsv",
            gs_key="test_prism_trial_id/run_2/wes_analysis/MHC_Class_I_filtered_condensed_ranked.tsv",
            upload_placeholder="032d8195-cde7-484f-aa56-25f950eeb1ad",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_2/run_2_tnscope.output.vcf",
            gs_key="test_prism_trial_id/run_2/wes_analysis/vcf_tnscope_output.vcf",
            upload_placeholder="478bb88c-ab41-4423-87d9-6e49ada70b96",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_2/run_2_tnscope.output.maf",
            gs_key="test_prism_trial_id/run_2/wes_analysis/maf_tnscope_output.maf",
            upload_placeholder="e73b8502-d7cc-4002-a96d-57e635f4f2b0",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_2/run_2_tnscope.filter.vcf",
            gs_key="test_prism_trial_id/run_2/wes_analysis/vcf_tnscope_filter.vcf",
            upload_placeholder="54466c04-86f8-44af-953d-0cfb10d11b33",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_2/run_2_tnscope.filter.maf",
            gs_key="test_prism_trial_id/run_2/wes_analysis/maf_tnscope_filter.maf",
            upload_placeholder="1d589bba-708c-449f-879f-44cba199c635",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_2/run_2_tnscope.filter.exons.broad.vcf.gz",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tnscope_exons_broad.gz",
            upload_placeholder="ba9d4b22-5610-4cde-b7e1-31ebf856a4ab",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_2/run_2_tnscope.filter.exons.mda.vcf.gz",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tnscope_exons_mda.gz",
            upload_placeholder="267e4b9f-e4b6-464a-bafb-44c0e405e44e",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/somatic/run_2/run_2_tnscope.filter.exons.mocha.vcf.gz",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tnscope_exons_mocha.gz",
            upload_placeholder="84f6bd4c-00db-4ce3-a6b6-a8482a333b25",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/corealignments/run_2/run_2_tn_corealigned.bam",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tn_corealigned.bam",
            upload_placeholder="9bad3bcb-1b37-4564-bd05-1a919b320f1b",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/corealignments/run_2/run_2_tn_corealigned.bam.bai",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tn_corealigned.bam.bai",
            upload_placeholder="4667eb84-13dd-4143-81f5-2e7272441daf",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/all_sample_summaries.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/all_summaries.txt",
            upload_placeholder="5dfc766a-d447-4279-abc4-3b93890b1e41",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/report/wes_version.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/wes_version.txt",
            upload_placeholder="46824763-fb9f-48b4-b7c4-7175759933f4",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP121.00/CTTTPP121.00_recalibrated.bam",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/recalibrated.bam",
            upload_placeholder="8d800118-9066-414f-a869-8d6574bdb803",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP121.00/CTTTPP121.00_recalibrated.bam.bai",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/recalibrated.bam.bai",
            upload_placeholder="47a180b1-8ce7-4268-ba8e-cc470610c812",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP121.00/CTTTPP121.00.sorted.dedup.bam",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/sorted.dedup.bam",
            upload_placeholder="d23d0858-eabb-4e9d-ad42-9bb4edadfd59",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP121.00/CTTTPP121.00.sorted.dedup.bam.bai",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/sorted.dedup.bam.bai",
            upload_placeholder="ea9a388b-d679-4a77-845f-2c4073425128",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00_coverage_metrics.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/coverage_metrics.txt",
            upload_placeholder="bc055607-9085-4f47-91e5-8f412c4dfafd",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00_target_metrics.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/target_metrics.txt",
            upload_placeholder="95e70b6a-1ddc-4bfe-84eb-6c4a6f1ee35d",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00_coverage_metrics.sample_summary.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/coverage_metrics_summary.txt",
            upload_placeholder="3db263fd-2b23-4905-8389-dc8c49c01c2f",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00_target_metrics.txt.sample_summary.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/target_metrics_summary.txt",
            upload_placeholder="3dd1b2c5-d5bd-44cc-b994-32cba3cab5d4",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00.broad.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/mosdepth_region_dist_broad.txt",
            upload_placeholder="3c5664be-f99a-406d-8849-8064d41a92fe",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00.mda.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/mosdepth_region_dist_mda.txt",
            upload_placeholder="a19d90c6-4794-4628-b1c8-dd603b7f6ff1",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00.mocha.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/mosdepth_region_dist_mocha.txt",
            upload_placeholder="2b3fbb1a-8182-4409-a90e-c69ee75cb194",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/optitype/CTTTPP121.00/CTTTPP121.00_result.tsv",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/optitype_result.tsv",
            upload_placeholder="671d710e-f245-4d2b-8732-2774e26aec10",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/xhla/CTTTPP121.00/CTTTPP121.00_report-CTTTPP121.00-hla.json",
            gs_key="test_prism_trial_id/run_2/wes_analysis/tumor/CTTTPP121.00/xhla_report_hla.json",
            upload_placeholder="4807aaa5-bafa-4fe5-89e9-73f9d734b971",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP121.00/CTTTPP121.00_recalibrated.bam",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/recalibrated.bam",
            upload_placeholder="d7ef5d2c-f2e8-469c-8666-c246ad74cf8b",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP121.00/CTTTPP121.00_recalibrated.bam.bai",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/recalibrated.bam.bai",
            upload_placeholder="1120d6c5-ee45-4612-a6e8-2f345ec2a719",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP121.00/CTTTPP121.00.sorted.dedup.bam",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/sorted.dedup.bam",
            upload_placeholder="f2b13d18-36a2-4273-a69c-a143415231db",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/align/CTTTPP121.00/CTTTPP121.00.sorted.dedup.bam.bai",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/sorted.dedup.bam.bai",
            upload_placeholder="4a06b799-2eb8-47f3-92fa-f5e21da85697",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00_coverage_metrics.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/coverage_metrics.txt",
            upload_placeholder="5566abb7-6bfb-4a0f-94a3-f3b02979a131",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00_target_metrics.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/target_metrics.txt",
            upload_placeholder="d92c402a-d9a5-4e6c-998d-b56b1b0b7ffa",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00_coverage_metrics.sample_summary.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/coverage_metrics_summary.txt",
            upload_placeholder="de83d3c9-6b0d-4317-b01e-dd28183744f7",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00_target_metrics.txt.sample_summary.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/target_metrics_summary.txt",
            upload_placeholder="cd4af4a4-da0d-4af9-b443-b5c15f85189b",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00.broad.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/mosdepth_region_dist_broad.txt",
            upload_placeholder="1ffc81e4-0b97-437d-85a8-9389b59727b5",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00.mda.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/mosdepth_region_dist_mda.txt",
            upload_placeholder="15933a57-70bf-4db0-b227-ab9ff5ce6258",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/metrics/CTTTPP121.00/CTTTPP121.00.mocha.mosdepth.region.dist.txt",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/mosdepth_region_dist_mocha.txt",
            upload_placeholder="c92dde2b-bf94-4b85-8185-2cf19fd5b7ee",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/optitype/CTTTPP121.00/CTTTPP121.00_result.tsv",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/optitype_result.tsv",
            upload_placeholder="9371d710-e3d0-4d1b-b87f-23bbadc4ae7e",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="analysis/xhla/CTTTPP121.00/CTTTPP121.00_report-CTTTPP121.00-hla.json",
            gs_key="test_prism_trial_id/run_2/wes_analysis/normal/CTTTPP121.00/xhla_report_hla.json",
            upload_placeholder="1d0c1f42-6a58-4e4b-b127-208c33f2aeb6",
            metadata_availability=None,
        ),
    ]

    cimac_ids = [
        sample["cimac_id"]
        for pair_run in prismify_patch["analysis"]["wes_analysis"]["pair_runs"]
        for sample in [pair_run["tumor"], pair_run["normal"]]
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
                }
            ]
        },
        "protocol_identifier": "test_prism_trial_id",
    }
    upload_entries = [
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/fcs.fcs",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/source.fcs",
            upload_placeholder="a5515c79-e5ff-41a8-bd98-c7e746a84d8c",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/assignment.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/assignment.csv",
            upload_placeholder="b54fc467-65d9-4cd3-baa7-9ec508ad56eb",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/comp.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/compartment.csv",
            upload_placeholder="1d2be563-3117-4a6a-9ad3-0351cae2b8c0",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/profiling.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/profiling.csv",
            upload_placeholder="3c8b9d95-b3c0-459b-84d3-6ee0b5c42b56",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/cca.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/cell_counts_assignment.csv",
            upload_placeholder="3b7f6d8a-811d-4213-8de3-b1fb92432c37",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/ccc.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/cell_counts_compartment.csv",
            upload_placeholder="0b0c9744-6065-4c0d-a595-a3db4f3605ec",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP111.00/ccp.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP111.00/cell_counts_profiling.csv",
            upload_placeholder="bd2588f3-b524-45b9-aba4-05d531a12bfe",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/fcs.fcs",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/source.fcs",
            upload_placeholder="26fb0ada-8860-4a3d-a278-6b04a36291b9",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/assignment.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/assignment.csv",
            upload_placeholder="662a59f1-361c-4cc1-8502-5155120b1ec2",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/comp.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/compartment.csv",
            upload_placeholder="dbcb4352-001a-45d4-bbaf-46f1832859f3",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/profiling.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/profiling.csv",
            upload_placeholder="cb714f63-2849-4916-9fe8-421331c08759",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/cca.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/cell_counts_assignment.csv",
            upload_placeholder="91cc578a-77f3-4898-84ab-e124f1cf000f",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/ccc.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/cell_counts_compartment.csv",
            upload_placeholder="46f88f77-07ec-46b9-9e9f-53532ae96efc",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="CTTTPP121.00/ccp.csv",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/CTTTPP121.00/cell_counts_profiling.csv",
            upload_placeholder="97634d45-5796-4210-80f6-c7f08c8f1e1d",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="batch1/reports.zip",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/reports.zip",
            upload_placeholder="5b09c736-0c99-4908-b288-41ebcc0a07d9",
            metadata_availability=None,
        ),
        LocalFileUploadEntry(
            local_path="batch1/analysis.zip",
            gs_key="test_prism_trial_id/cytof_analysis/test_prism_trial_id_run_1/XYZ1/analysis.zip",
            upload_placeholder="6abb7949-5400-4e5a-a947-5a1403ca75cb",
            metadata_availability=None,
        ),
    ]

    cimac_ids = [
        record["cimac_id"]
        for batch in prismify_patch["assays"]["cytof"]
        for record in batch["records"]
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


missing = set(SUPPORTED_ANALYSES).difference(
    [f.__name__ for f in analysis_data_generators]
)
assert not missing, f"Missing analysis test data generators for {missing}"
