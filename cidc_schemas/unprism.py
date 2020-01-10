"""Tools from extracting information from trial metadata blobs."""
from io import StringIO, BytesIO
from typing import Callable, NamedTuple, Optional, Union

from pandas.io.json import json_normalize

from . import prism

FileStream = Union[StringIO, BytesIO]


class DeriveFilesContext(NamedTuple):
    fetch_artifact: Callable[[str], Optional[FileStream]]
    save_artifact: Callable[[str, FileStream], None]


class FileDerivation:
    def run(self, trial_metadata: dict, context: DeriveFilesContext):
        """Execute the file derivation."""
        raise NotImplementedError("No derivation implemented for this upload type.")


def derive_files(trial_metadata: dict, upload_type: str, context: DeriveFilesContext):
    """Derive files from a trial_metadata blob given an `upload_type`"""
    # Select the derivation for this upload type
    derivation: FileDerivation = FileDerivation()
    if upload_type in prism.SUPPORTED_SHIPPING_MANIFESTS:
        derivation = ShippingManifestDerivation()

    # Run the derivation
    derivation.run(trial_metadata, context)


class ShippingManifestDerivation(FileDerivation):
    """Derive files from a shipping manifest upload."""

    def run(self, trial_metadata: dict, context: DeriveFilesContext):
        trial_id = trial_metadata[prism.PROTOCOL_ID_FIELD_NAME]
        participants_csv = self._participants_csv(trial_metadata)
        samples_csv = self._samples_csv(trial_metadata)

        context.save_artifact(f"{trial_id}/participants.csv", participants_csv)
        context.save_artifact(f"{trial_id}/samples.csv", samples_csv)

    def _participants_csv(self, trial_metadata: dict) -> StringIO:
        """Return a CSV of patient-level metadata for the given trial."""
        participants = json_normalize(
            data=trial_metadata,
            record_path=["participants"],
            meta=[prism.PROTOCOL_ID_FIELD_NAME],
        )

        participants.drop("samples", axis=1, inplace=True, errors="ignore")

        return StringIO(participants.to_csv(index=False))

    def _samples_csv(self, trial_metadata: dict) -> StringIO:
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

        return StringIO(samples.to_csv(index=False))
