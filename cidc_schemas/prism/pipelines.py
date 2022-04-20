"""Analysis pipeline configuration generators."""
import csv
import io

import logging
from typing import Dict, List, NamedTuple
from datetime import datetime
from collections import defaultdict

from ..util import load_pipeline_config_template, participant_id_from_cimac
from .constants import PROTOCOL_ID_FIELD_NAME

logger = logging.getLogger(__file__)


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
        Based on sequencing quality, choose which cimac_id to use
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
                            f"Cannot figure out sample type (normal vs *tumor) for {cimac_id}: {processed_sample_derivative}"
                        )
                        partic_map[cimac_participant_id]["tumors"][
                            collection_event_name
                        ].append(cimac_id)

        # revert to pure dicts to throw KeyError if something happens elsewhere
        for partic_dict in partic_map.values():
            partic_dict["tumors"] = dict(partic_dict["tumors"])
        return dict(partic_map)

    def __call__(self, full_ct: dict, patch: dict, bucket: str) -> Dict[str, str]:
        """
        Generates a mapping from run_ids to the
        generated snakemake wes .yaml configs.

        Patch is expected to be already merged into full_ct.
        """

        class AnalysisRun(NamedTuple):
            """ontainer class for possible runs to report"""

            tumor_cimac_id: str
            normal_cimac_id: str = None
            run_id: str = None

        potential_new_runs: List[AnalysisRun] = []  # to be rendered

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
                    potential_new_runs.append(AnalysisRun(tum_i, norm_i, runi))
                    new_data_ids.difference([norm_i, tum_i])

            # the rest of the new IDs could be possible tumor_only runs
            for new_id in new_data_ids:
                potential_new_runs.append(AnalysisRun(new_id))

        elif self.upload_type == "pairing":
            # first we filter cimac_ids for which we now got pairing info
            # from analysis runs.
            potential_new_runs = [
                AnalysisRun(
                    r["tumor"]["cimac_id"], r["normal"]["cimac_id"], r["run_id"]
                )
                for r in patch["analysis"]["wes_analysis"]["pair_runs"]
            ]

        # then we compose a list of all records from all assay runs,
        # so we can filter out analysis runs for which we have data for both samples
        all_wes_records = {}
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

        file_content: str = (
            f"{PROTOCOL_ID_FIELD_NAME},{full_ct[PROTOCOL_ID_FIELD_NAME]}\n"
        )
        file_content += "tumor,tumor_collection_event,normal,normal_collection_event\n"
        file_content += "\n".join([",".join(entry) for entry in tumor_pair_list])

        res = {}
        res[full_ct[PROTOCOL_ID_FIELD_NAME] + "_pairing.csv"] = file_content
        for run in potential_new_runs:
            # if we have data files for *both* items in a tumor/normal pair
            if (
                run.normal_cimac_id
                and run.normal_cimac_id in all_wes_records
                and run.tumor_cimac_id in all_wes_records
            ):
                # then this is a run we need, and so we render it
                res[run.run_id + ".yaml"] = self.analysis_config.render(
                    **{
                        "run_id": run.run_id,
                        "tumor_sample": all_wes_records[run.tumor_cimac_id],
                        "normal_sample": all_wes_records[run.normal_cimac_id],
                        "BIOFX_BUCKET_NAME": bucket,
                    }
                )

            # if there's no matching normal or doesn't have the files,
            # render it as a tumor_only sample if we have its data files
            elif run.tumor_cimac_id in all_wes_records:
                # use tumor CIMAC ID as run_id if not given (formatted in jinja)
                run_id = run.run_id if run.run_id else run.tumor_cimac_id
                res[run_id + ".yaml"] = self.tumor_only_analysis_config.render(
                    **{
                        "run_id": run_id,
                        "tumor_sample": all_wes_records[run.tumor_cimac_id],
                        "BIOFX_BUCKET_NAME": bucket,
                    }
                )

        return res


def _csv2string(data):
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerows(data)
    return si.getvalue().strip("\r\n")


RNA_METASHEET_KEYS = [
    "cimac_id",
    "cimac_participant_id",
    "collection_event_name",
    "type_of_sample",
    "processed_sample_derivative",
]


def _extract_sample_metadata(participants, records):
    per_participant_cimac_ids = defaultdict(set)
    for record in records:
        cid = record["cimac_id"]
        pid = participant_id_from_cimac(cid)

        per_participant_cimac_ids[pid].add(cid)

    all_participants = {
        participant["cimac_participant_id"]: participant["samples"]
        for participant in participants
    }

    sample_metadata = {}
    # we expect to be guaranteed that all cimac_ids in the `patch` to be present
    # in `full_ct` sample set, because they should have been created by previous manifest upload
    for pid, cimac_ids_list in per_participant_cimac_ids.items():
        for sample in all_participants[pid]:
            cid = sample["cimac_id"]
            if cid in cimac_ids_list:
                sample_metadata[cid] = dict(sample, cimac_participant_id=pid)

    return sample_metadata


def _rna_level1_pipeline_config(
    full_ct: dict, patch: dict, bucket: str
) -> Dict[str, str]:
    """
    Generates .yaml configs for RNAseq pipeline and a metasheet.csv with sample metadata.
    Returns a filename to file content map.

    Patch is expected to be already merged into full_ct.
    """

    tid = full_ct[PROTOCOL_ID_FIELD_NAME]

    templ = load_pipeline_config_template("rna_level1_analysis_config")

    # as we know that `patch` is a prism result of a rna_fastq upload
    # we are sure these getitem calls should be fine
    # and that there should be just one rna assay
    assay = patch["assays"]["rna"][0]

    dt = datetime.now().isoformat(timespec="minutes").replace(":", "-")

    # now we collect metadata for every sample in the patch
    sample_metadata = _extract_sample_metadata(
        full_ct["participants"], assay["records"]
    )

    res = {
        f"metasheet_{tid}_{dt}.csv": _csv2string(
            [RNA_METASHEET_KEYS]
            + [[s.get(k) for k in RNA_METASHEET_KEYS] for s in sample_metadata.values()]
        )
    }

    config_str = templ.render(
        BIOFX_BUCKET_NAME=bucket,
        samples=assay["records"],
        paired_end_reads=assay["paired_end_reads"],
        dt=dt,
    )
    # keying on participant id and date time, so if data for one participant
    # comes in different uploads, those runs will be distinguishable
    res[f"rna_pipeline_{tid}_{dt}.yaml"] = config_str

    return res


# This is a map from a assay type to a config generators,
# that should take (full_ct: dict, patch: dict, bucket: str) as arguments
# and return a map {"file_name": ["whatever pipeline config is"]}
_ANALYSIS_CONF_GENERATORS = {
    "wes_fastq": _Wes_pipeline_config("assay"),
    "wes_bam": _Wes_pipeline_config("assay"),
    "tumor_normal_pairing": _Wes_pipeline_config("pairing"),
    "rna_fastq": _rna_level1_pipeline_config,
    "rna_bam": _rna_level1_pipeline_config,
}


def generate_analysis_configs_from_upload_patch(
    ct: dict, patch: dict, template_type: str, bucket: str
) -> Dict[str, str]:
    """
    Generates all needed pipeline configs, from a new upload info.
    Args:
        ct: full metadata object *with `patch` merged*!
        patch: metadata patch passed from upload (assay or manifest)
        template_type: assay or manifest type
        bucket: a name of a bucket where data files are expected to be
                available for the pipeline runner
    Returns:
        Filename to pipeline configs as a string map.
    """

    if template_type not in _ANALYSIS_CONF_GENERATORS:
        return {}

    return _ANALYSIS_CONF_GENERATORS[template_type](ct, patch, bucket)
