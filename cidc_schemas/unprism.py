"""Tools from extracting information from trial metadata blobs."""
from typing import Callable, NamedTuple, Optional, AnyStr, Union, ByteString, List

from pandas.io.json import json_normalize

from . import prism

StrOrBytes = Union[str, bytes]


class DeriveFilesContext(NamedTuple):
    # fetch_artifact should return None if no artifact is found
    fetch_artifact: Callable[[str], Optional[StrOrBytes]]
    # TODO: add new attributes as needed?


class Artifact(NamedTuple):
    object_url: str
    data: StrOrBytes
    metadata: Optional[dict]


class DeriveFilesResult(NamedTuple):
    artifacts: List[Artifact]
    trial_metadata: dict


def derive_files(
    trial_metadata: dict, upload_type: str, context: DeriveFilesContext
) -> DeriveFilesResult:
    """Derive files from a trial_metadata blob given an `upload_type`"""
    # Select the derivation for this upload type
    derivation: FileDerivation = FileDerivation()
    if upload_type in prism.SUPPORTED_SHIPPING_MANIFESTS:
        derivation = ShippingManifestDerivation()

    return derivation.run(trial_metadata, context)


class FileDerivation:
    def run(
        self, trial_metadata: dict, context: DeriveFilesContext
    ) -> DeriveFilesResult:
        """Execute the file derivation."""
        raise NotImplementedError("No derivation implemented for this upload type.")


class ShippingManifestDerivation(FileDerivation):
    """Derive files from a shipping manifest upload."""

    def run(self, trial_metadata: dict, context: DeriveFilesContext):
        trial_id = trial_metadata[prism.PROTOCOL_ID_FIELD_NAME]
        participants_csv = self._participants_csv(trial_metadata)
        samples_csv = self._samples_csv(trial_metadata)

        return DeriveFilesResult(
            [
                Artifact(f"{trial_id}/participants.csv", participants_csv),
                Artifact(f"{trial_id}/samples.csv", samples_csv),
            ],
            trial_metadata,  # return metadata without updates
        )

    def _participants_csv(self, trial_metadata: dict) -> str:
        """Return a CSV of patient-level metadata for the given trial."""
        participants = json_normalize(
            data=trial_metadata,
            record_path=["participants"],
            meta=[prism.PROTOCOL_ID_FIELD_NAME],
        )

        participants.drop("samples", axis=1, inplace=True, errors="ignore")

        return participants.to_csv(index=False)

    def _samples_csv(self, trial_metadata: dict) -> str:
        """Return a CSV of patient-level metadata for the given trial."""
        samples = json_normalize(
            data=trial_metadata,
            record_path=["participants", "samples"],
            meta=[
                prism.PROTOCOL_ID_FIELD_NAME,
                ["participants", "cimac_participant_id"],
            ],
        )

        samples.drop("aliquots", axis=1, inplace=True, errors="ignore")

        return samples.to_csv(index=False)
