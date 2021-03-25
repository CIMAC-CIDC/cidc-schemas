import os
import pstats
import cProfile
import argparse
from contextlib import contextmanager

from tqdm import tqdm

from cidc_schemas.template import Template
from cidc_schemas.template_reader import XlTemplateReader
from cidc_schemas.prism import (
    merge_clinical_trial_metadata,
    merge_artifacts,
    ArtifactInfo,
    prismify,
    set_prism_encrypt_key,
)


@contextmanager
def profiling(run_name: str, outdir: str = "benchmark"):
    """A context manager that profiles enclosed code using cProfile.Profile,
    outputting results to the specified output director (defaults to "benchmark/").
    """
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    profiler = cProfile.Profile()
    profiler.enable()
    exception = None
    try:
        print(f"Running step '{run_name}'")
        yield
    except Exception as e:
        exception = e
    finally:
        profiler.disable()
        filename = os.path.join(outdir, f"{run_name}.profile.txt")
        with open(filename, "w") as outfile:
            outfile.write(f"[profiler output for '{run_name}']\n\n")
            ps = pstats.Stats(profiler, stream=outfile).sort_stats("time")
            ps.print_stats()
        print(f"Wrote profiler results to {filename}")
        if exception:
            raise exception


def run(ts_path: str, mif_path: str, he_path: str):
    """Run and profile a typical metadata validation and merging workload."""
    set_prism_encrypt_key("foobar")

    with profiling("prismify_tissue_slide_shipping_manifest"):
        ts_template = Template.from_type("tissue_slide")
        ts_spreadsheet, _ = XlTemplateReader.from_excel(ts_path)
        ts_metadata, _, _ = prismify(ts_spreadsheet, ts_template)
        ts_metadata["allowed_cohort_names"] = ["Not_reported"]
        ts_metadata["allowed_collection_event_names"] = ["Baseline"]

    with profiling("prismify_mif_assay_metadata_spreadsheet"):
        mif_template = Template.from_type("mif")
        mif_spreadsheet, _ = XlTemplateReader.from_excel(mif_path)
        mif_metadata, files, _ = prismify(mif_spreadsheet, mif_template)

    with profiling("merge_mif_assay_artifacts_into_mif_metadata_patch"):
        # tqdm gives us a stdout progress indicator as prism iterates through the array
        artifact_info = tqdm(
            [
                ArtifactInfo(
                    f.upload_placeholder,
                    f"object/url/{f.upload_placeholder}",
                    "",
                    0,
                    "",
                    "abcd",
                )
                for i, f in enumerate(files)
            ]
        )
        mif_metadata, _ = merge_artifacts(mif_metadata, artifact_info)

    with profiling("merge_mif_metadata_with_tissue_slide_metadata"):
        combined_metadata, _ = merge_clinical_trial_metadata(mif_metadata, ts_metadata)

    # Don't profile this a second time, since we're only interested
    # in how long it takes to merge the shipping manifest data into
    # existing trial metadata
    he_template = Template.from_type("h_and_e")
    he_spreadsheet, _ = XlTemplateReader.from_excel(he_path)
    he_metadata, _, _ = prismify(he_spreadsheet, he_template)

    with profiling("merge_h_and_e_metadata_into_trial"):
        merge_clinical_trial_metadata(he_metadata, combined_metadata)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run and profile a typical metadata validation and merging workload."
    )
    parser.add_argument(
        "--ts-path", required=True, help="path to a tissue slide metadata spreadsheet"
    )
    parser.add_argument(
        "--mif-path",
        required=True,
        help="path to an mif metadata spreadsheet with samples from the tissue slide manifest",
    )
    parser.add_argument(
        "--he-path", required=True, help="path to an h&e metadata spreadsheet"
    )
    args = parser.parse_args()

    run(args.ts_path, args.mif_path, args.he_path)
