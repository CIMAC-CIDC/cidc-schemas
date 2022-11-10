"""Analysis pipeline configuration generators."""
from collections import defaultdict
from datetime import datetime
from io import BytesIO
import logging
from tempfile import NamedTemporaryFile
from typing import Dict, List, NamedTuple, Union

import jinja2
import pandas as pd

from .constants import PROTOCOL_ID_FIELD_NAME, SUPPORTED_SHIPPING_MANIFESTS
from ..template import Template
from ..util import load_pipeline_config_template, participant_id_from_cimac

logger = logging.getLogger(__file__)

# Note, bucket names must be all lowercase, dash, and underscore
# https://cloud.google.com/storage/docs/naming-buckets#requirements
def RNA_GOOGLE_BUCKET_PATH_FN(trial_id: str, batch_num: int) -> str:
    return f"gs://repro_{trial_id.lower()}/RNA/set{batch_num+1}"


def RNA_INSTANCE_NAME_FN(trial_id: str, batch_num: int) -> str:
    return f"rima_{trial_id}_set{batch_num+1}"


def BIOFX_WES_ANALYSIS_FOLDER(trial_id: str, cimac_id: str) -> str:
    return f"gs://repro_{trial_id}/WES_v3/{cimac_id}/analysis"


def WES_GOOGLE_BUCKET_PATH_FN(trial_id: str, run_id: str) -> str:
    return f"gs://repro_{trial_id.lower()}/WES_v3/{run_id}"


def WES_CONCAT_FASTQ_PATH_FN(trial_id: str, cimac_id: str, read: int) -> str:
    return f"gs://repro_{trial_id.lower()}/WES/fastq/concat_all/analysis/concat/{cimac_id}_R{read}.fastq.gz"


RNA_INGESTION_FOLDER: str = "/mnt/ssd/rima/analysis/"
RNA_SAMPLES_PER_CONFIG: int = 4
WES_SAMPLES_PER_CONFIG: int = 20

WES_CONFIG_COLUMN_NAMES: List[str] = [
    "tumor_cimac_id",
    "normal_cimac_id",
    "google_bucket_path",
    "tumor_fastq_path_pair1",
    "tumor_fastq_path_pair2",
    "normal_fastq_path_pair1",
    "normal_fastq_path_pair2",
    "rna_bam_file",
    "rna_expression_file",
    "cimac_center",
    "cores",
    "disk_size",
    "wes_commit",
    "image",
    "wes_ref_snapshot",
    "somatic_caller",
    "trim_soft_clip",
    "tumor_only",
    "zone",
]


class _AnalysisRun(NamedTuple):
    """container class for possible runs to report"""

    run_id: str
    tumor_cimac_id: str
    normal_cimac_id: str = None


class _PairingEntry(NamedTuple):
    """container class for entries to the pairing.csv"""

    tumor_cimac_id: str = ""
    tumor_collection_event: str = ""
    legacy_tumor_only: bool = False
    previously_excluded: bool = False
    normal_cimac_id: str = ""
    normal_collection_event: str = ""
    legacy_normal: bool = False


class _Wes_pipeline_config:
    def __init__(self, upload_type: str):
        """
        A function that for specified assay type will
        generate a snakemake .yaml for each tumor/normal pair and
        tumor-only (ie unpaired) samples with .fastq or bam available.

        upload_type == "assay" is for when the upload consists of .fastq/.bam assay data.
        So sample_id's for which we now have data should be in the `patch` arg,
        and corresponding sample pairing info should be in the `full_ct` doc.

        Or if upload_type == "pairing" it's vice versa - new runs/pairs are calculated
        from `patch` (which is a "pairing"), and then we look for sample data info in
        the `full_ct`

        Briefly:
        - we need to figure out what new data we've got
        - based on that, find candidate analysis runs (tumor/normal pairs and unpaired samples),
            that we might need to run now, due to new data arived.
        - last step actually check if for each candidate we have assay data
            for both - normal and tumor sample - and we render tumor/normal pipeline config for those
            and tumor_only config otherwise

        As a result each assay or tumor_normal_pairing upload that "completes" some
        analysis run/pair (making all 3 pieces available - both samples data and a pairing)
        will be rendered only once - right after that upload.

        Patch is expected to be already merged into full_ct.
        """
        if upload_type not in ["assay", "pairing"]:
            raise NotImplementedError(
                f"Not supported type:{upload_type} for wes pipeline config generation."
            )
        self.upload_type = upload_type

    def _choose_which_normal(self, full_ct: dict, cimac_ids: List[str]) -> str:
        """
        TODO Based on sequencing quality, choose which cimac_id to use
        Currently just returns the first of the list
        """
        return sorted(cimac_ids)[0]

    def _generate_partic_map(
        self,
        full_ct: dict,
    ) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Return a structure for matching tumor/normal samples semiautomatically.
        Normal/Germline samples are deduplicated per patient for each collection_event_name.
            see _Wes_pipeline_config._choose_which_normal() above
        All Tumor samples are returned.

        If a sample can't be determined, returned as Tumor

        Parameters
        ----------
        full_ct: dict
            the full metadata JSON for the clinical trial
        cimac_id_list: List[str]
            a list of the CIMAC IDs to look at

        Returns
        -------
        {
            cimac_participant_id str: {
                "tumors":  {collection_event_name str: [cimac_id str, ...], ...},
                "normals": {collection_event_name str: cimac_id str, ...},
            },
            ...
        }
        """
        partic_map = defaultdict(lambda: {"tumors": defaultdict(list), "normals": {}})
        for partic in full_ct["participants"]:
            cimac_participant_id = partic["cimac_participant_id"]
            for sample in partic["samples"]:
                cimac_id = sample["cimac_id"]
                if cimac_id in self.all_wes_samples:
                    collection_event_name = sample["collection_event_name"]
                    processed_sample_derivative = sample.get(
                        "processed_sample_derivative", ""
                    )

                    if processed_sample_derivative == "Germline DNA":
                        other_cimac_id = partic_map[cimac_participant_id][
                            "normals"
                        ].pop(collection_event_name, "")
                        if other_cimac_id:
                            cimac_id = self._choose_which_normal(
                                full_ct, cimac_ids=[cimac_id, other_cimac_id]
                            )
                        partic_map[cimac_participant_id]["normals"][
                            collection_event_name
                        ] = cimac_id

                    elif processed_sample_derivative == "Tumor DNA":
                        partic_map[cimac_participant_id]["tumors"][
                            collection_event_name
                        ].append(cimac_id)

                    else:
                        logger.warning(
                            f"Cannot figure out sample type (normal vs tumor) for {cimac_id}: {processed_sample_derivative}"
                        )
                        partic_map[cimac_participant_id]["tumors"][
                            collection_event_name
                        ].append(cimac_id)

        # revert to pure dicts to throw KeyError if something happens elsewhere
        for partic_dict in partic_map.values():
            partic_dict["tumors"] = dict(partic_dict["tumors"])
        return dict(partic_map)

    def _generate_template_excel(
        self,
        trial_id: str,
        run: _AnalysisRun,
    ) -> bytes:
        """
        Generates the Excel upload template for the given WES analysis run
        """
        with NamedTemporaryFile() as tmp:
            # if we have data files for *both* items in a tumor/normal pair
            if run.normal_cimac_id and run.normal_cimac_id in self.all_wes_samples:
                workbook = self.wes_analysis_template.to_excel(tmp.name, close=False)
                worksheet = workbook.get_worksheet_by_name("WES Analysis")

                worksheet.write(1, 2, trial_id)
                worksheet.write(
                    2, 2, BIOFX_WES_ANALYSIS_FOLDER(trial_id, run.tumor_cimac_id)
                )
                worksheet.write(6, 1, run.run_id)
                worksheet.write(6, 2, run.normal_cimac_id)
                worksheet.write(6, 3, run.tumor_cimac_id)

                workbook.close()

            # if there's no matching normal or doesn't have the files,
            # render it as a tumor_only sample if we have its data files
            else:
                workbook = self.wes_tumor_only_analysis_template.to_excel(
                    tmp, close=False
                )
                worksheet = workbook.get_worksheet_by_name("WES tumor-only Analysis")

                worksheet.write(1, 2, trial_id)
                worksheet.write(
                    2, 2, BIOFX_WES_ANALYSIS_FOLDER(trial_id, run.tumor_cimac_id)
                )
                worksheet.write(6, 1, run.run_id)
                worksheet.write(6, 2, run.tumor_cimac_id)

                workbook.close()

            tmp.seek(0)
            ret: bytes = tmp.read()
        return ret

    def _pair_all_samples(
        self, partic_map: Dict[str, Dict[str, Dict[str, str]]]
    ) -> List[_PairingEntry]:
        """
        (Semi)automated pairing of tumor and normal samples

        Parameters
        ----------
        partic_map: Dict[str, Dict[str, List[str]]]
        {
            cimac_participant_id str: {
                "tumors":  {collection_event_name str: [cimac_id str, ...], ...},
                "normals": {collection_event_name str: cimac_id str, ...},
            },
            ...
        }
            as returned by participant

        Returns
        -------
            List[(
                tumor_cimac_id: str, tumor_collection_event: str,
                normal_cimac_id: str, normal_collection_event: str
            )]
                one entry for each pair, unmatched tumor, and unmatched normal
                if not paired, values are empty ie ""
        """
        tumor_pair_list = []
        for partic in partic_map:
            tumors = partic_map[partic]["tumors"]
            normals = partic_map[partic]["normals"]
            matched_normals = []
            for collection_event in tumors:
                for sample in tumors[collection_event]:
                    # if the sample has already been analyzed in a pair,
                    # don't include it in the pairing.csv
                    if sample in self.wes_analysis_tumor_samples:
                        continue
                    elif len(normals) == 1:
                        tumor_pair_list.append(
                            _PairingEntry(
                                tumor_cimac_id=sample,
                                tumor_collection_event=collection_event,
                                legacy_tumor_only=sample
                                in self.wes_tumor_only_analysis_samples,
                                previously_excluded=sample in self.excluded_samples,
                                normal_cimac_id=list(normals.values())[0],
                                normal_collection_event=list(normals.keys())[0],
                                legacy_normal=list(normals.values())[0]
                                in self.wes_analysis_normal_samples,
                            )
                        )
                        matched_normals.append(list(normals.values())[0])
                    elif len(normals) > 1:
                        if collection_event in normals.keys():
                            tumor_pair_list.append(
                                _PairingEntry(
                                    tumor_cimac_id=sample,
                                    tumor_collection_event=collection_event,
                                    legacy_tumor_only=sample
                                    in self.wes_tumor_only_analysis_samples,
                                    previously_excluded=sample in self.excluded_samples,
                                    normal_cimac_id=normals[collection_event],
                                    normal_collection_event=collection_event,
                                    legacy_normal=normals[collection_event]
                                    in self.wes_analysis_normal_samples,
                                )
                            )
                            matched_normals.append(normals[collection_event])
                        elif "Baseline" in normals.keys():
                            tumor_pair_list.append(
                                _PairingEntry(
                                    tumor_cimac_id=sample,
                                    tumor_collection_event=collection_event,
                                    legacy_tumor_only=sample
                                    in self.wes_tumor_only_analysis_samples,
                                    previously_excluded=sample in self.excluded_samples,
                                    normal_cimac_id=normals["Baseline"],
                                    normal_collection_event="Baseline",
                                    legacy_normal=normals["Baseline"]
                                    in self.wes_analysis_normal_samples,
                                )
                            )
                            matched_normals.append(normals["Baseline"])
                        else:
                            tumor_pair_list.append(
                                _PairingEntry(
                                    tumor_cimac_id=sample,
                                    tumor_collection_event=collection_event,
                                    legacy_tumor_only=sample
                                    in self.wes_tumor_only_analysis_samples,
                                    previously_excluded=sample in self.excluded_samples,
                                )
                            )
                    else:
                        tumor_pair_list.append(
                            _PairingEntry(
                                tumor_cimac_id=sample,
                                tumor_collection_event=collection_event,
                                legacy_tumor_only=sample
                                in self.wes_tumor_only_analysis_samples,
                                previously_excluded=sample in self.excluded_samples,
                            )
                        )

            for collection_event in normals:
                if normals[collection_event] not in matched_normals:
                    tumor_pair_list.append(
                        _PairingEntry(
                            normal_cimac_id=normals[collection_event],
                            normal_collection_event=collection_event,
                            legacy_normal=normals[collection_event]
                            in self.wes_analysis_normal_samples,
                        )
                    )

        return tumor_pair_list

    def _generate_batch_config(
        self,
        trial_id: str,
        batch_runs: List[_AnalysisRun],
        data_bucket: str,
    ) -> bytes:
        df = pd.DataFrame(columns=WES_CONFIG_COLUMN_NAMES)

        for n, run in enumerate(batch_runs):
            assay_creator: str = self.all_wes_samples[run.tumor_cimac_id][
                "assay_creator"
            ]
            if assay_creator not in ["MD Anderson", "Broad"]:
                raise Exception(
                    f"assay_creator for WES expected to be either MD Anderson or Broad, not: {assay_creator}\n"
                    f"Trial {trial_id}, run {run.run_id}, sample {run.tumor_cimac_id}"
                )
            cimac_center: str = "broad" if assay_creator == "Broad" else "mda"

            to_append: dict = {
                "tumor_cimac_id": run.tumor_cimac_id,
                "normal_cimac_id": run.normal_cimac_id,  # None if empty
                "google_bucket_path": WES_GOOGLE_BUCKET_PATH_FN(
                    trial_id=trial_id, run_id=run.run_id
                ),
                "cimac_center": cimac_center,
                "cores": 64,
                "disk_size": 500,
                "wes_commit": "21376c4",
                "image": "wes-ver3-01c",
                "wes_ref_snapshot": "wes-human-ref-ver1-8",
                "somatic_caller": "tnscope",
                "trim_soft_clip": False,
                "tumor_only": run.normal_cimac_id is None,
                "zone": "us-east1-c",
            }

            tumor_files: dict = self.all_wes_samples[run.tumor_cimac_id]["files"]
            if "r1" in tumor_files:
                to_append.update(
                    {
                        "tumor_fastq_path_pair1": WES_CONCAT_FASTQ_PATH_FN(
                            trial_id=trial_id, cimac_id=run.tumor_cimac_id, read=1
                        ),
                        "tumor_fastq_path_pair2": WES_CONCAT_FASTQ_PATH_FN(
                            trial_id=trial_id, cimac_id=run.tumor_cimac_id, read=2
                        ),
                    }
                )
            else:  # if "bam" in tumor_files
                to_append.update(
                    {
                        "tumor_fastq_path_pair1": f"gs://{data_bucket}/{tumor_files['bam'][0]['object_url']}",
                        "tumor_fastq_path_pair2": "",
                    }
                )

            if run.normal_cimac_id and run.normal_cimac_id in self.all_wes_samples:
                normal_files: dict = self.all_wes_samples[run.normal_cimac_id]["files"]
                if "r1" in normal_files:
                    to_append.update(
                        {
                            "normal_fastq_path_pair1": WES_CONCAT_FASTQ_PATH_FN(
                                trial_id=trial_id, cimac_id=run.normal_cimac_id, read=1
                            ),
                            "normal_fastq_path_pair2": WES_CONCAT_FASTQ_PATH_FN(
                                trial_id=trial_id, cimac_id=run.normal_cimac_id, read=2
                            ),
                        }
                    )
                else:  # if "bam" in normal_files
                    to_append.update(
                        {
                            "normal_fastq_path_pair1": f"gs://{data_bucket}/{normal_files['bam'][0]['object_url']}",
                            "normal_fastq_path_pair2": "",
                        }
                    )

            df.loc[n] = to_append

        # write the config to bytes via BytesIO
        ret = BytesIO()
        df.to_excel(ret, index=False)
        ret.seek(0)

        return ret.read()

    def _generate_pairing_csv(
        self, trial_id: str, tumor_pair_list: List[_PairingEntry]
    ) -> str:
        file_content: str = f"{PROTOCOL_ID_FIELD_NAME},{trial_id}\n"
        file_content += "tumor,tumor_collection_event,legacy_tumor_only,previously_excluded,normal,normal_collection_event,legacy_normal\n"
        file_content += "\n".join(
            [
                ",".join(
                    [
                        (str(e).upper() if e else "") if isinstance(e, bool) else e
                        for e in entry
                    ]
                )
                for entry in tumor_pair_list
            ]
        )
        return file_content

    def _handle_batch_config_and_sheets(
        self,
        trial_id: str,
        batch_num: int,
        data_bucket: str,
    ) -> Dict[str, bytes]:
        res: Dict[str, bytes] = {}
        # don't go too far and IndexError
        end_idx: int = min(
            len(self.potential_new_runs),
            WES_SAMPLES_PER_CONFIG * (batch_num + 1),
        )
        batch_runs = self.potential_new_runs[
            WES_SAMPLES_PER_CONFIG * batch_num : end_idx
        ]

        res[
            f"wes_ingestion_{trial_id}.batch_{batch_num+1}_of_{self.num_batches}.{self.timestamp}.xlsx"
        ] = self._generate_batch_config(
            trial_id=trial_id,
            batch_runs=batch_runs,
            data_bucket=data_bucket,
        )

        # generate each ingestion sheet separately
        for run in batch_runs:
            # _generate_template_excel handles paired vs tumor-only
            res[
                f"{run.run_id}.template.{trial_id}.batch_{batch_num+1}_of_{self.num_batches}.{self.timestamp}.xlsx"
            ] = self._generate_template_excel(
                trial_id=trial_id,
                run=run,
            )

        return res

    def _generate_configs_and_ingestion_sheets(
        self,
        trial_id: str,
        patch: dict,
        data_bucket: str,
    ) -> Dict[str, bytes]:
        res: Dict[str, bytes] = {}
        # find all the potential new runs to be rendered
        # both paired samples (first by biofx preference)
        # AND tumor-only samples
        self.potential_new_runs: List[_AnalysisRun] = [
            _AnalysisRun(r["run_id"], r["tumor"]["cimac_id"], r["normal"]["cimac_id"])
            for r in patch["analysis"].get("wes_analysis", {}).get("pair_runs")
        ] + [
            _AnalysisRun(r["run_id"], r["tumor"]["cimac_id"])
            for r in patch["analysis"].get("wes_tumor_only_analysis", {}).get("runs")
        ]

        # chunk into batches for config generation
        self.num_batches: int = len(
            self.potential_new_runs
        ) // WES_SAMPLES_PER_CONFIG + (
            # as this is integer division, we need one more for any leftovers
            1
            if len(self.potential_new_runs) % WES_SAMPLES_PER_CONFIG
            # if exact multiple, don't have any leftovers for a trailing batch
            else 0
        )
        self.timestamp: str = (
            datetime.now().isoformat(timespec="minutes").replace(":", "-")
        )
        self.wes_analysis_template = Template.from_type("wes_analysis")
        self.wes_tumor_only_analysis_template = Template.from_type(
            "wes_tumor_only_analysis"
        )
        for batch_num in range(self.num_batches):
            res.update(
                self._handle_batch_config_and_sheets(
                    trial_id=trial_id, batch_num=batch_num, data_bucket=data_bucket
                )
            )

        return res

    def __call__(
        self, full_ct: dict, patch: dict, data_bucket: str
    ) -> Dict[str, Union[bytes, str]]:
        """
        Generates a mapping from filename to the files to attach.
        Attachments differ depending on whether the upload is wes_[bam/fastq] vs tumor_normal_pairing
        For wes_[bam/faq]:
            generates a pairing.csv file attempting to pair WES samples
        For tumor_normal_pairing:
            generates a pairing.csv file attempting to pair WES samples
            generates WES Monitor .yaml configs for each batch of 20 affected samples
            generates ingestion .xlsx templates for each affected sample
                for paired samples, for wes_analysis
                for unpaired samples, for wes_tumor_only_analysis

        For the pairing.csv
            - tumor samples already in a paired analysis are ignored
            - flag for tumor samples already in a tumor-only analysis
            - flag for normal samples already in a paired analysis

        Patch is expected to be already merged into full_ct.
        """
        # compose a list of all CIMAC IDs from all assay runs
        # so we can filter out analysis runs for which we have data for both samples
        # only keep ones we have assay files for
        self.all_wes_samples: Dict[str, dict] = {
            # also note the assay_creator because we would need that for WES config generation
            # assay_creator required on assays/wes entry
            r["cimac_id"]: dict(assay_creator=wes["assay_creator"], **r)
            for wes in full_ct["assays"]["wes"]
            for r in wes["records"]
            if "files" in r
        }

        # unlike wes assay, we can't be sure there's any analysis already loaded
        # so all of the below use .get() everywhere except for required values

        self.excluded_samples: List[str] = []
        for infix in ["", "_tumor_only"]:
            for suffix in ["", "_old"]:
                key: str = f"wes{infix}_analysis{suffix}"
                self.excluded_samples.extend(
                    excluded["cimac_id"]
                    for excluded in full_ct.get("analysis", {})
                    .get(key, {})
                    .get("excluded_samples", [])
                )

        self.wes_analysis_tumor_samples: List[str] = [
            pair["tumor"]["cimac_id"]
            for pair in (
                full_ct.get("analysis", {}).get("wes_analysis", {}).get("pair_runs", [])
                + full_ct.get("analysis", {})
                .get("wes_analysis_old", {})
                .get("pair_runs", [])
            )
            if "report" in pair
        ]
        self.wes_analysis_normal_samples: List[str] = [
            pair["normal"]["cimac_id"]
            for pair in (
                full_ct.get("analysis", {}).get("wes_analysis", {}).get("pair_runs", [])
                + full_ct.get("analysis", {})
                .get("wes_analysis_old", {})
                .get("pair_runs", [])
            )
            if "report" in pair
        ]
        self.wes_tumor_only_analysis_samples: List[str] = [
            run["tumor"]["cimac_id"]
            for run in (
                full_ct.get("analysis", {})
                .get("wes_tumor_only_analysis", {})
                .get("runs", [])
                + full_ct.get("analysis", {})
                .get("wes_tumor_only_analysis_old", {})
                .get("runs", [])
            )
            if "report" in run
        ]

        # classify all of the WES records as tumor or normal and get collection event name
        # in preparation for (semi)automated pairing
        # partic_map = {
        #     cimac_participant_id str: {
        #         "tumors": {cimac_id str: collection_event_name str},
        #         "normals": {cimac_id str: collection_event_name str},
        #     }
        # }
        partic_map = self._generate_partic_map(full_ct)

        # (semi)automated pairing of tumor and normal samples
        # as partic_map is generated using only the WES samples,
        # it's the same as pairing all samples
        tumor_pair_list: List[_PairingEntry] = self._pair_all_samples(partic_map)

        # Begin preparing response
        # {filename: contents}
        trial_id: str = full_ct[PROTOCOL_ID_FIELD_NAME]
        res: Dict[str, str] = {
            # add a pairing sheet for new runs
            trial_id
            + "_pairing.csv": self._generate_pairing_csv(trial_id, tumor_pair_list)
        }

        # for tumor_normal_pairing, also generate configs and ingestion sheets
        if "pairing" in self.upload_type:
            res.update(
                self._generate_configs_and_ingestion_sheets(
                    trial_id=trial_id,
                    patch=patch,
                    data_bucket=data_bucket,
                )
            )

        return res


def _generate_rna_template_excel(
    trial_id: str,
    rna_records: Dict[str, dict],
    rnaseq_analysis_template: Template,
) -> bytes:
    """
    Generates the Excel upload template for the given RNA analysis run
    """
    worksheet_name: str = [
        wk
        for wk in rnaseq_analysis_template.schema["properties"]["worksheets"]
        if wk.lower().startswith("rna")
    ][0]

    with NamedTemporaryFile() as tmp:
        workbook = rnaseq_analysis_template.to_excel(tmp.name, close=False)
        worksheet = workbook.get_worksheet_by_name(worksheet_name)

        worksheet.write(1, 2, trial_id)
        worksheet.write(2, 2, RNA_INGESTION_FOLDER)

        for n, sample in enumerate(rna_records):
            worksheet.write(6 + n, 1, sample["cimac_id"])

        workbook.close()

        tmp.seek(0)
        ret: bytes = tmp.read()
    return ret


def _rna_level1_pipeline_config(
    full_ct: dict, patch: dict, data_bucket: str
) -> Dict[str, Union[bytes, str]]:
    """
    Generates .yaml configs for RNAseq pipeline.
    Returns a filename to file content map.

    Patch is expected to be already merged into full_ct.
    """

    trial_id: str = full_ct[PROTOCOL_ID_FIELD_NAME]

    templ: jinja2.Template = load_pipeline_config_template("rna_level1_analysis_config")
    rnaseq_level1_analysis_template: Template = Template.from_type(
        "rna_level1_analysis"
    )

    # as we know that `patch` is a prism result of a rna_[fastq/bam] upload
    # we are sure these getitem calls should be fine
    # and that there should be just one rna assay
    assay: dict = patch["assays"]["rna"][0]

    timestamp: str = datetime.now().isoformat(timespec="minutes").replace(":", "-")

    res: Dict[str, str] = {}

    # separate into chunks of samples and render them in batches
    num_batches: int = len(assay["records"]) // RNA_SAMPLES_PER_CONFIG + 1
    for batch_num in range(num_batches):
        instance_name: str = RNA_INSTANCE_NAME_FN(
            trial_id=trial_id, batch_num=batch_num
        )
        google_bucket_path: str = RNA_GOOGLE_BUCKET_PATH_FN(
            trial_id=trial_id, batch_num=batch_num
        )

        samples: List[dict] = assay["records"][
            batch_num
            * 4 : min(RNA_SAMPLES_PER_CONFIG * (batch_num + 1), len(assay["records"]))
        ]

        # keying on trial_id and timestamp, so configs from reupload will be distinguishable
        res[
            f"rna_pipeline_{trial_id}.batch_{batch_num+1}_of_{num_batches}.{timestamp}.yaml"
        ] = templ.render(
            participant_id_from_cimac=participant_id_from_cimac,
            data_bucket=data_bucket,
            google_bucket_path=google_bucket_path,
            instance_name=instance_name,
            samples=samples,
        )
        res[
            f"rna_ingestion_{trial_id}.batch_{batch_num+1}_of_{num_batches}.{timestamp}.xlsx"
        ] = _generate_rna_template_excel(
            trial_id=trial_id,
            rna_records=samples,
            rnaseq_analysis_template=rnaseq_level1_analysis_template,
        )

    return res


def _tcr_pipeline_config(
    full_ct: dict, patch: dict, data_bucket: str
) -> Dict[str, str]:
    """
    Generates meta.csv with sample metadata config for TCRseq pipeline.
    Returns a filename to file content map.

    Patch is expected to be already merged into full_ct.
    """

    trial_id: str = full_ct[PROTOCOL_ID_FIELD_NAME]

    # as we know that `patch` is a prism result of a tcr_[adaptive/fastq] upload
    # we are sure these getitem calls should be fine
    # and that there should be just one tcr assay
    assay: dict = patch["assays"]["tcr"][0]
    batch_id = assay["batch_id"]

    file_content: str = "sample,batch\n"
    file_content += "\n".join(
        [",".join([record["cimac_id"], batch_id]) for record in assay["records"]]
    )

    # add a meta sheet for new runs
    return {f"{trial_id}_{batch_id}_meta.csv": file_content}


def _shipping_manifest_new_participants(
    full_ct: dict, patch: dict, data_bucket: str
) -> Dict[str, str]:
    """
    Parameters
    ----------
    ct: dict
        full metadata object *with `patch` merged*!
    patch: dict
        metadata patch passed from manifest upload
    """
    sample_count = {
        partic["cimac_participant_id"]: len(partic["samples"])
        for partic in full_ct["participants"]
    }

    # if all of the samples are new, this is a new participant
    new_participant_ids: List[str] = []
    for partic in patch["participants"]:
        if len(partic["samples"]) == sample_count[partic["cimac_participant_id"]]:
            new_participant_ids.append(partic["cimac_participant_id"])

    if len(new_participant_ids):
        return {"new_participants.txt": "\n".join(new_participant_ids)}
    else:
        return {}


# This is a map from a assay type to a config generators,
# that should take (full_ct: dict, patch: dict, data_bucket: str) as arguments
# and return a map {"file_name": ["whatever pipeline config is"]}
_ANALYSIS_CONF_GENERATORS = {
    "wes_fastq": _Wes_pipeline_config("assay"),
    "wes_bam": _Wes_pipeline_config("assay"),
    "tcr_adaptive": _tcr_pipeline_config,
    "tcr_fastq": _tcr_pipeline_config,
    "tumor_normal_pairing": _Wes_pipeline_config("pairing"),
    "rna_fastq": _rna_level1_pipeline_config,
    "rna_bam": _rna_level1_pipeline_config,
}


def generate_analysis_configs_from_upload_patch(
    ct: dict, patch: dict, template_type: str, data_bucket: str
) -> Dict[str, str]:
    """
    Generates all needed pipeline configs, from a new upload info.
    Args:
        ct: full metadata object *with `patch` merged*!
        patch: metadata patch passed from upload (assay or manifest)
        template_type: assay or manifest type
        data_bucket: a name of a data_bucket where data files are expected to be
                available for the pipeline runner
    Returns:
        Filename to pipeline configs as a string map.
    """
    ret = {}

    if template_type in SUPPORTED_SHIPPING_MANIFESTS:
        ret.update(_shipping_manifest_new_participants(ct, patch, data_bucket))

    if template_type in _ANALYSIS_CONF_GENERATORS:
        ret.update(_ANALYSIS_CONF_GENERATORS[template_type](ct, patch, data_bucket))

    return ret
