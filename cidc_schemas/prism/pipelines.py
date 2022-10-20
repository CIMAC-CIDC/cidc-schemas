"""Analysis pipeline configuration generators."""
from collections import defaultdict
from datetime import datetime
import logging
from tempfile import NamedTemporaryFile
from typing import Dict, List, NamedTuple, Tuple, Union

import jinja2

from .constants import PROTOCOL_ID_FIELD_NAME, SUPPORTED_SHIPPING_MANIFESTS
from ..template import Template
from ..util import load_pipeline_config_template, participant_id_from_cimac

BIOFX_WES_ANALYSIS_FOLDER: str = "/mnt/ssd/wes/analysis"
logger = logging.getLogger(__file__)


def RNA_GOOGLE_BUCKET_PATH_FN(trial_id: str, batch_num: int) -> str:
    return f"gs://repro_{trial_id}/RNA/set{batch_num+1}"


def RNA_INSTANCE_NAME_FN(trial_id: str, batch_num: int) -> str:
    return f"rima_{trial_id}_set{batch_num+1}"


RNA_INGESTION_FOLDER: str = "/mnt/ssd/rima/analysis/"


class _AnalysisRun(NamedTuple):
    """container class for possible runs to report"""

    tumor_cimac_id: str
    normal_cimac_id: str = None
    run_id: str = None


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

        self.analysis_config = load_pipeline_config_template("wes_analysis_config")
        self.tumor_only_analysis_config = load_pipeline_config_template(
            "wes_tumor_only_analysis_config"
        )

    def _choose_which_normal(self, full_ct: dict, cimac_ids: List[str]) -> str:
        """
        TODO Based on sequencing quality, choose which cimac_id to use
        Currently just returns the first of the list
        """
        return sorted(cimac_ids)[0]

    def _generate_partic_map(
        self, full_ct: dict, cimac_id_list: List[str]
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
                if cimac_id in cimac_id_list:
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
        all_wes_records: Dict[str, dict],
        wes_analysis_template: Template,
        wes_tumor_only_analysis_template: Template,
    ) -> bytes:
        """
        Generates the Excel upload template for the given WES analysis run
        """
        with NamedTemporaryFile() as tmp:
            # use tumor CIMAC ID as run_id if not given
            run_id = run.run_id if run.run_id else run.tumor_cimac_id

            # if we have data files for *both* items in a tumor/normal pair
            if (
                run.normal_cimac_id
                and run.normal_cimac_id in all_wes_records
                and run.tumor_cimac_id in all_wes_records
            ):
                workbook = wes_analysis_template.to_excel(tmp.name, close=False)
                worksheet = workbook.get_worksheet_by_name("WES Analysis")

                worksheet.write(1, 2, trial_id)
                worksheet.write(2, 2, BIOFX_WES_ANALYSIS_FOLDER)
                worksheet.write(6, 1, run_id)
                worksheet.write(6, 2, run.normal_cimac_id)
                worksheet.write(6, 3, run.tumor_cimac_id)

                workbook.close()

            # if there's no matching normal or doesn't have the files,
            # render it as a tumor_only sample if we have its data files
            elif run.tumor_cimac_id in all_wes_records:
                workbook = wes_tumor_only_analysis_template.to_excel(tmp, close=False)
                worksheet = workbook.get_worksheet_by_name("WES tumor-only Analysis")

                worksheet.write(1, 2, trial_id)
                worksheet.write(2, 2, BIOFX_WES_ANALYSIS_FOLDER)
                worksheet.write(6, 1, run_id)
                worksheet.write(6, 2, run.tumor_cimac_id)

                workbook.close()

            tmp.seek(0)
            ret: bytes = tmp.read()
        return ret

    def _find_potential_runs(self, full_ct: dict, patch: dict) -> List[_AnalysisRun]:
        potential_new_runs: List[_AnalysisRun] = []  # to be returned
        if self.upload_type == "assay":
            # first we search for cimac_ids for which we just got new data files
            new_data_ids = set()
            # as we know that `patch` is a prism result of a wes upload
            # we are sure these getitem calls should be fine
            for wes in patch["assays"]["wes"]:
                for r in wes["records"]:
                    new_data_ids.add(r["cimac_id"])

            # then we compose a list of all the analysis runs
            # which are also cimac_ids tumor/normal pairs.
            for r in (
                full_ct.get("analysis", {})
                .get("wes_analysis", {})
                .get("pair_runs", [])
                # this notation is used due to that we don't know if we have any "analyses"
                # or any pairs in them. Thus we provide default empty containers.
            ):
                norm_i = r["normal"]["cimac_id"]
                tum_i = r["tumor"]["cimac_id"]
                runi = r["run_id"]
                # we filter runs, for which we have new data for at least on of the samples:
                if norm_i in new_data_ids or tum_i in new_data_ids:
                    potential_new_runs.append(_AnalysisRun(tum_i, norm_i, runi))
                    new_data_ids.difference([norm_i, tum_i])

            # the rest of the new IDs could be possible tumor_only runs
            for new_id in new_data_ids:
                potential_new_runs.append(_AnalysisRun(new_id))

        elif self.upload_type == "pairing":
            # first we filter cimac_ids for which we now got pairing info
            # from analysis runs.
            potential_new_runs = [
                _AnalysisRun(
                    r["tumor"]["cimac_id"], r["normal"]["cimac_id"], r["run_id"]
                )
                for r in patch["analysis"]["wes_analysis"]["pair_runs"]
            ]

        return potential_new_runs

    def _pair_all_samples(
        self, partic_map: Dict[str, Dict[str, Dict[str, str]]]
    ) -> List[Tuple[str, str, str, str]]:
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
                    if len(normals) == 1:
                        tumor_pair_list.append(
                            (
                                sample,
                                collection_event,
                                list(normals.values())[0],
                                list(normals.keys())[0],
                            )
                        )
                        matched_normals.append(list(normals.values())[0])
                    elif len(normals) > 1:
                        if collection_event in normals.keys():
                            tumor_pair_list.append(
                                (
                                    sample,
                                    collection_event,
                                    normals[collection_event],
                                    collection_event,
                                )
                            )
                            matched_normals.append(normals[collection_event])
                        elif "Baseline" in normals.keys():
                            tumor_pair_list.append(
                                (
                                    sample,
                                    collection_event,
                                    normals["Baseline"],
                                    "Baseline",
                                )
                            )
                            matched_normals.append(normals["Baseline"])
                        else:
                            tumor_pair_list.append((sample, collection_event, "", ""))
                    else:
                        tumor_pair_list.append((sample, collection_event, "", ""))

            for collection_event in normals:
                if normals[collection_event] not in matched_normals:
                    tumor_pair_list.append(
                        ("", "", normals[collection_event], collection_event)
                    )

        return tumor_pair_list

    def _generate_run_config(
        self, run: _AnalysisRun, all_wes_records: Dict[str, dict], data_bucket: str
    ) -> str:
        # if we have data files for *both* items in a tumor/normal pair
        if (
            run.normal_cimac_id
            and run.normal_cimac_id in all_wes_records
            and run.tumor_cimac_id in all_wes_records
        ):
            # then this is a run we need, and so we render it
            return self.analysis_config.render(
                **{
                    "run_id": run.run_id,
                    "tumor_sample": all_wes_records[run.tumor_cimac_id],
                    "normal_sample": all_wes_records[run.normal_cimac_id],
                    "BIOFX_BUCKET_NAME": data_bucket,
                }
            )

        # if there's no matching normal or doesn't have the files,
        # render it as a tumor_only sample if we have its data files
        elif run.tumor_cimac_id in all_wes_records:
            # use tumor CIMAC ID as run_id if not given (formatted in jinja)
            run_id = run.run_id if run.run_id else run.tumor_cimac_id
            return self.tumor_only_analysis_config.render(
                **{
                    "run_id": run_id,
                    "tumor_sample": all_wes_records[run.tumor_cimac_id],
                    "BIOFX_BUCKET_NAME": data_bucket,
                }
            )

    def _generate_pairing_csv(
        self, trial_id: str, tumor_pair_list: List[Tuple[str, str, str, str]]
    ) -> str:
        file_content: str = f"{PROTOCOL_ID_FIELD_NAME},{trial_id}\n"
        file_content += "tumor,tumor_collection_event,normal,normal_collection_event\n"
        file_content += "\n".join([",".join(entry) for entry in tumor_pair_list])
        return file_content

    def __call__(
        self, full_ct: dict, patch: dict, data_bucket: str
    ) -> Dict[str, Union[bytes, str]]:
        """
        Generates a mapping from filename to the files to attach.
        For each run_id, there is:
            a generated snakemake wes config f"{run_id}.yaml"
            a generated template for analysis ingestion f"{run_id}.template.xlsx"

        Patch is expected to be already merged into full_ct.
        """
        # find all the potential new runs to be rendered
        potential_new_runs: List[_AnalysisRun] = self._find_potential_runs(
            full_ct, patch
        )

        # then we compose a list of all records from all assay runs,
        # so we can filter out analysis runs for which we have data for both samples
        all_wes_records: Dict[str, dict] = dict()
        for wes in full_ct["assays"]["wes"]:
            for r in wes["records"]:
                all_wes_records[r["cimac_id"]] = r

        # classify all of the WES records as tumor or normal and get collection event name
        # in preparation for (semi)automated pairing
        # partic_map = {
        #     cimac_participant_id str: {
        #         "tumors": {cimac_id str: collection_event_name str},
        #         "normals": {cimac_id str: collection_event_name str},
        #     }
        # }
        partic_map = self._generate_partic_map(full_ct, all_wes_records.keys())

        # (semi)automated pairing of tumor and normal samples
        # as partic_map is generated using only the WES samples,
        # it's the same as pairing all samples
        tumor_pair_list = self._pair_all_samples(partic_map)

        # Begin preparing response
        # {filename: contents}
        res: Dict[str, str] = {
            # add a pairing sheet for new runs
            full_ct[PROTOCOL_ID_FIELD_NAME]
            + "_pairing.csv": self._generate_pairing_csv(
                full_ct[PROTOCOL_ID_FIELD_NAME], tumor_pair_list
            )
        }

        # for each run, generate the config and upload template
        wes_analysis_template = Template.from_type("wes_analysis")
        wes_tumor_only_analysis_template = Template.from_type("wes_tumor_only_analysis")
        for run in potential_new_runs:
            run_id: str = run.run_id if run.run_id else run.tumor_cimac_id
            res[run_id + ".yaml"] = self._generate_run_config(
                run,
                all_wes_records=all_wes_records,
                data_bucket=data_bucket,
            )
            res[run_id + ".template.xlsx"] = self._generate_template_excel(
                trial_id=full_ct[PROTOCOL_ID_FIELD_NAME],
                run=run,
                all_wes_records=all_wes_records,
                wes_analysis_template=wes_analysis_template,
                wes_tumor_only_analysis_template=wes_tumor_only_analysis_template,
            )

        return res


def _generate_rna_template_excel(
    trial_id: str,
    rna_records: Dict[str, dict],
    rnaseq_analysis_template: Template,
) -> bytes:
    """
    Generates the Excel upload template for the given WES analysis run
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
    Generates .yaml configs for RNAseq pipeline and a metasheet.csv with sample metadata.
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

    # separate into chunks of (up to) 4 samples and render them in batches
    num_batches: int = len(assay["records"]) // 4 + 1
    for batch_num in range(num_batches):
        instance_name: str = RNA_INSTANCE_NAME_FN(
            trial_id=trial_id, batch_num=batch_num
        )
        google_bucket_path: str = RNA_GOOGLE_BUCKET_PATH_FN(
            trial_id=trial_id, batch_num=batch_num
        )

        samples: List[dict] = assay["records"][
            batch_num * 4 : min(batch_num * 4 + 4, len(assay["records"]))
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
