"""Analysis pipeline configuration generators."""

from typing import List, NamedTuple, Dict, Callable

from ..util import load_pipeline_config_template


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
                        "tumor_sample": all_wes_records[run.normal_cimac_id],
                        "normal_sample": all_wes_records[run.tumor_cimac_id],
                        "BIOFX_BUCKET_NAME": bucket,
                    }
                )

        return res

    return internal


def _rnaseq_pipeline_config(full_ct: dict, patch: dict, bucket: str) -> Dict[str, str]:
    """
        Generates a .yaml config for RNAseq pipeline 
        
        Patch is expected to be already merged into full_ct.
    """

    templ = load_pipeline_config_template("rnaseq_analysis_config")

    # as we know that `patch` is a prism result of a rna_fastq upload
    # we are sure these getitem calls should be fine
    new_data = [r for assay in patch["assays"]["rna"] for r in assay["records"]]

    res = {}
    for sample_data in new_data:
        res[sample_data["cimac_id"] + ".yaml"] = templ.render(
            BIOFX_BUCKET_NAME=bucket, **sample_data
        )

    return res


# This is a map from a assay type to a config generators,
# that should take (full_ct: dict, patch: dict, bucket: str) as arguments
# and return a map {"file_name": ["whatever pipeline config is"]}
_ANALYSIS_CONF_GENERATORS = {
    "wes_fastq": _wes_pipeline_config("assay"),
    "wes_bam": _wes_pipeline_config("assay"),
    "tumor_normal_pairing": _wes_pipeline_config("pairing"),
    "rna_fastq": _rnaseq_pipeline_config,
    "rna_bam": _rnaseq_pipeline_config,
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
