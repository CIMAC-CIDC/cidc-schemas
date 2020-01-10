"""Tools from extracting information from trial metadata blobs."""
from typing import Callable, NamedTuple, Optional, AnyStr, Union, ByteString, List

from pandas.io.json import json_normalize

from . import prism

StrOrBytes = Union[str, bytes]


class DeriveFilesContext(NamedTuple):
    trial_metadata: dict
    upload_type: str
    # fetch_artifact should return None if no artifact is found
    fetch_artifact: Callable[[str], Optional[StrOrBytes]]
    # TODO: add new attributes as needed?


class Artifact(NamedTuple):
    object_url: str
    data: StrOrBytes
    file_type: str
    data_format: str
    metadata: Optional[dict]


class DeriveFilesResult(NamedTuple):
    artifacts: List[Artifact]
    trial_metadata: dict


_per_assay_derivations = {}


def derive_files(context: DeriveFilesContext) -> DeriveFilesResult:
    """Derive files from a trial_metadata blob given an `upload_type`"""
    if context.upload_type in prism.SUPPORTED_SHIPPING_MANIFESTS:
        return _shipping_manifest_derivation(context)

    if context.upload_type in _per_assay_derivations:
        return _per_assay_derivations[context.upload_type](context)

    raise NotImplementedError(
        f"No file derivations for upload type {context.upload_type}"
    )


def _build_artifact(
    context: DeriveFilesContext,
    file_name: str,
    data: StrOrBytes,
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
                "participants.csv",
                "participants info",
                "csv",
                participants_csv,
            ),
            _build_artifact(context, "samples.csv", "samples info", "csv", samples_csv),
        ],
        context.trial_metadata,  # return metadata without updates
    )


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


_per_assay_derivations["ihc"] = _ihc_derivation
