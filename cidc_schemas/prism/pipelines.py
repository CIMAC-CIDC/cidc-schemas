"""Analysis pipeline configuration generators."""
import csv
import io

from typing import List, NamedTuple, Dict, Callable
from datetime import datetime
from collections import defaultdict

from ..util import load_pipeline_config_template, participant_id_from_cimac
from .constants import PROTOCOL_ID_FIELD_NAME


def _wes_pipeline_config(
    upload_type: str,
) -> Callable[[dict, dict, str], Dict[str, str]]:
    """
        Returns a function that for specified assay type will
        generate a snakemake .yaml for each tumor/normal pair with
        .fastq or bam available. 

        upload_type == "assay" is for when the upload consists of .fastq/.bam assay data.
        So sample_id's for which we now have data should be in the `patch` arg,  
        and corresponding sample pairing info should be in the `full_ct` doc.

        Or if upload_type == "pairing" it's vice versa - new runs/pairs are calculated 
        from `patch` (which is a "pairing"), and then we look for sample data info in 
        the `full_ct`  

        In brush strokes it goes like this:
        - we need to figure out what new data we've got
        - based on that we calculate candidate analysis runs (tumor/normal pairs),
          that we might need to run now, due to new data arived.
        - last step actually check if for each candidate we have assay data
          for both - normal and tumor sample - and we render pipeline configs for those.

        As a result each assay or tumor_normal_pairing upload that "completes" some
        analysis run/pair (making all 3 pieces available - both samples data and a pairing)
        will be rendered only once - right after that upload.

        Patch is expected to be already merged into full_ct.
    """
    if upload_type not in ["assay", "pairing"]:
        raise NotImplementedError(
            f"Not supported type:{upload_type} for wes pipeline config generation."
        )

    templ = load_pipeline_config_template("wes_analysis_config")

    class AnalysisRun(NamedTuple):
        normal_cimac_id: str
        tumor_cimac_id: str
        run_id: str

    def internal(full_ct: dict, patch: dict, bucket: str) -> Dict[str, str]:
        """
            Generates a map from analysis run_ids found in full_ct
            to generated snakemake wes .yaml configs. 

            Patch is expected to be already merged into full_ct.
        """

        potential_new_runs: List[AnalysisRun] = []  # to be rendered

        if upload_type == "assay":
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
                    potential_new_runs.append(AnalysisRun(norm_i, tum_i, runi))

        if upload_type == "pairing":
            # first we filter cimac_ids for which we now got pairing info
            # from analysis runs.
            potential_new_runs = [
                AnalysisRun(
                    r["normal"]["cimac_id"], r["tumor"]["cimac_id"], r["run_id"]
                )
                for r in patch["analysis"]["wes_analysis"]["pair_runs"]
            ]

        # then we compose a list of all records from all assay runs,
        # so we can filter out analysis runs for which we have data for both samples
        all_wes_records = {}
        for wes in full_ct["assays"]["wes"]:
            for r in wes["records"]:
                all_wes_records[r["cimac_id"]] = r

        res = {}
        for run in potential_new_runs:
            # if we have data files for *both* items in a tumor/normal pair
            if (
                run.normal_cimac_id in all_wes_records
                and run.tumor_cimac_id in all_wes_records
            ):
                # then this is a run we need, and so we render it
                res[run.run_id + ".yaml"] = templ.render(
                    **{
                        "run_id": run.run_id,
                        "tumor_sample": all_wes_records[run.tumor_cimac_id],
                        "normal_sample": all_wes_records[run.normal_cimac_id],
                        "BIOFX_BUCKET_NAME": bucket,
                    }
                )

        return res

    return internal


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
        Generates .yaml configs for RNAseq pipeline and a metasheet.csv with sampels metadata.
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
    "wes_fastq": _wes_pipeline_config("assay"),
    "wes_bam": _wes_pipeline_config("assay"),
    "tumor_normal_pairing": _wes_pipeline_config("pairing"),
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
