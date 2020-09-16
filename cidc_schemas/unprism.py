"""Tools from extracting information from trial metadata blobs."""
from io import StringIO, BytesIO
from typing import Callable, NamedTuple, Optional, Union, List, Dict

import pandas as pd
from pandas.io.json import json_normalize

from . import prism
from .util import participant_id_from_cimac


class DeriveFilesContext(NamedTuple):
    trial_metadata: dict
    upload_type: str
    # fetch_artifact:
    #   * should return None if no artifact is found.
    #   * arg1 (str): object_url
    #   * arg2 (bool): if True, return artifact as StringIO, otherwise BytesIO.
    fetch_artifact: Callable[[str, bool], Optional[Union[StringIO, BytesIO]]]
    # TODO: add new attributes as needed?


class Artifact(NamedTuple):
    object_url: str
    data: Union[str, bytes]
    file_type: str
    data_format: str
    metadata: Optional[dict]


class DeriveFilesResult(NamedTuple):
    artifacts: List[Artifact]
    trial_metadata: dict


_upload_type_derivations: Dict[
    str, Callable[[DeriveFilesContext], DeriveFilesResult]
] = {}


def _register_derivation(upload_type: str):
    """Bind an upload type to a function that generates its file derivations."""

    def decorator(f):
        _upload_type_derivations[upload_type] = f
        return f

    return decorator


def derive_files(context: DeriveFilesContext) -> DeriveFilesResult:
    """Derive files from a trial_metadata blob given an `upload_type`"""
    if context.upload_type in prism.MANIFESTS_WITH_PARTICIPANT_INFO:
        return _shipping_manifest_derivation(context)

    if context.upload_type in _upload_type_derivations:
        return _upload_type_derivations[context.upload_type](context)

    raise NotImplementedError(
        f"No file derivations for upload type {context.upload_type}"
    )


def _build_artifact(
    context: DeriveFilesContext,
    file_name: str,
    data: Union[str, bytes],
    file_type: str,
    data_format: str,
    metadata: Optional[dict] = None,
    include_upload_type: bool = False,
) -> Artifact:
    """Generate an Artifact object for the given arguments within a DeriveFilesContext."""
    trial_id = context.trial_metadata[prism.PROTOCOL_ID_FIELD_NAME]

    if include_upload_type:
        object_url = f"{trial_id}/{context.upload_type}/{file_name}"
    else:
        object_url = f"{trial_id}/{file_name}"

    return Artifact(
        object_url=object_url,
        data=data,
        file_type=file_type,
        data_format=data_format,
        metadata=metadata,
    )


def _shipping_manifest_derivation(context: DeriveFilesContext) -> DeriveFilesResult:
    """Generate files derived from a shipping manifest upload."""
    participants = json_normalize(
        data=context.trial_metadata,
        record_path=["participants"],
        meta=[prism.PROTOCOL_ID_FIELD_NAME],
    )
    samples = json_normalize(
        data=context.trial_metadata,
        record_path=["participants", "samples"],
        meta=[prism.PROTOCOL_ID_FIELD_NAME, ["participants", "cimac_participant_id"]],
    )

    participants.drop("samples", axis=1, inplace=True, errors="ignore")
    samples.drop("aliquots", axis=1, inplace=True, errors="ignore")

    participants_csv = participants.to_csv(index=False)
    samples_csv = samples.to_csv(index=False)

    return DeriveFilesResult(
        [
            _build_artifact(
                context,
                file_name="participants.csv",
                file_type="participants info",
                data_format="csv",
                data=participants_csv,
            ),
            _build_artifact(
                context,
                file_name="samples.csv",
                file_type="samples info",
                data_format="csv",
                data=samples_csv,
            ),
        ],
        context.trial_metadata,  # return metadata without updates
    )


@_register_derivation("ihc")
def _ihc_derivation(context: DeriveFilesContext) -> DeriveFilesResult:
    """Generate a combined CSV for IHC data"""
    combined = json_normalize(
        data=context.trial_metadata,
        record_path=["assays", "ihc", "records"],
        meta=[prism.PROTOCOL_ID_FIELD_NAME],
    )

    # remove all artifact related columns
    combined.drop(
        [c for c in combined.columns if c.startswith("files.")],
        axis=1,
        inplace=True,
        errors="ignore",
    )

    combined_csv = combined.to_csv(index=False)

    return DeriveFilesResult(
        [
            _build_artifact(
                context,
                "combined.csv",
                combined_csv,
                "ihc marker combined",
                "csv",
                include_upload_type=True,
            )
        ],
        context.trial_metadata,  # return metadata without updates
    )


@_register_derivation("wes_analysis")
def _wes_analysis_derivation(context: DeriveFilesContext) -> DeriveFilesResult:
    """Generate a combined MAF file for an entire trial"""
    # Extract all run-level MAF URLs for this trial
    runs = json_normalize(
        data=context.trial_metadata,
        record_path=["analysis", "wes_analysis", "pair_runs"],
    )
    maf_urls = runs["somatic.maf_tnscope_filter.object_url"]

    def download_and_parse_maf(maf_url: str) -> Optional[pd.DataFrame]:
        maf_stream = context.fetch_artifact(maf_url, True)
        if maf_stream:
            # First row will contain a comment, not headers, so skip it
            return pd.read_csv(maf_stream, sep="\t", skiprows=1)
        return None

    # Download all sample-level MAF files as dataframes
    maf_dfs = maf_urls.apply(download_and_parse_maf)

    # Combine all sample-level MAF dataframes
    combined_maf_df = pd.concat(maf_dfs.values, join="outer")

    # Write the combined dataframe to tab-separated string
    combined_maf = combined_maf_df.to_csv(sep="\t", index=False)

    return DeriveFilesResult(
        [
            _build_artifact(
                context,
                file_name="combined.maf",
                data=combined_maf,
                file_type="combined maf",
                data_format="maf",
                include_upload_type=True,
            )
        ],
        context.trial_metadata,  # return metadata without updates
    )


@_register_derivation("cytof_analysis")
def _cytof_analysis_derivation(context: DeriveFilesContext) -> DeriveFilesResult:
    """Generate a combined CSV for CyTOF analysis data"""
    cell_counts_analysis_csvs = json_normalize(
        data=context.trial_metadata,
        record_path=["assays", "cytof", "records"],
        meta=[prism.PROTOCOL_ID_FIELD_NAME],
    )

    artifacts = []
    for combined_f_kind in [
        "cell_counts_assignment",
        "cell_counts_compartment",
        "cell_counts_profiling",
    ]:
        res_df = pd.DataFrame()
        for index, row in cell_counts_analysis_csvs.iterrows():
            obj_url = row[f"output_files.{combined_f_kind}.object_url"]

            cell_counts_csv = context.fetch_artifact(obj_url, True)

            if not cell_counts_csv:
                raise Exception(
                    f"Failed to read {obj_url} building Cytof analysis derivation"
                )

            df = pd.read_csv(cell_counts_csv)

            # Each cell_counts_... file consist of just records for one sample.
            # The first column of each cell_counts_csv (CellSubset) contains cell group types
            # and the second contains counts for those types.
            # Create a new, transposed dataframe with cell group types as column headers
            # and a single row of cell count data.
            df = df.set_index("CellSubset")
            df = df.drop(
                columns="Unnamed: 0", axis=1
            )  # Cell counts files contain an unnamed index column
            df = df.transpose()

            # and adding metadata, so we can distinguish different samples
            df = df.rename(index={"N": row["cimac_id"]})
            df["cimac_id"] = row["cimac_id"]
            df["cimac_participant_id"] = participant_id_from_cimac(row["cimac_id"])
            df[prism.PROTOCOL_ID_FIELD_NAME] = row[prism.PROTOCOL_ID_FIELD_NAME]

            # finally combine them
            res_df = pd.concat([res_df, df])

        # and add as artifact
        artifacts.append(
            _build_artifact(
                context=context,
                file_name=f"combined_{combined_f_kind}.csv",
                data=res_df.to_csv(index=False),
                data_format="csv",  # confusing, but right
                file_type=combined_f_kind.replace("_", " "),
                include_upload_type=True,
            )
        )

    return DeriveFilesResult(
        artifacts, context.trial_metadata  # return metadata without updates
    )
