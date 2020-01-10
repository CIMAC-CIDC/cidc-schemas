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
    derivation: FileDerivation = FileDerivation(trial_metadata, upload_type, context)
    if upload_type in prism.SUPPORTED_SHIPPING_MANIFESTS:
        derivation = ShippingManifestDerivation(trial_metadata, upload_type, context)

    return derivation.run()


class FileDerivation:
    def __init__(
        self, trial_metadata: dict, upload_type: str, context: DeriveFilesContext
    ):
        self.trial_metadata = trial_metadata
        self.upload_type = upload_type
        self.context = context

    def run(self) -> DeriveFilesResult:
        """Execute the file derivation."""
        raise NotImplementedError("No derivation implemented for this upload type.")

    def build_artifact(
        self,
        file_name: str,
        data: StrOrBytes,
        metadata: Optional[dict] = None,
        include_upload_type: bool = False,
    ) -> Artifact:
        """Generate an Artifact object."""
        trial_id = self.trial_metadata[prism.PROTOCOL_ID_FIELD_NAME]

        if include_upload_type:
            object_url = f"{trial_id}/{self.upload_type}/{file_name}"
        else:
            object_url = f"{trial_id}/{file_name}"

        return Artifact(object_url, data, metadata)


class ShippingManifestDerivation(FileDerivation):
    """Derive files from a shipping manifest upload."""

    def run(self):
        participants_csv = self._participants_csv()
        samples_csv = self._samples_csv()

        return DeriveFilesResult(
            [
                self.build_artifact("participants.csv", participants_csv),
                self.build_artifact("samples.csv", samples_csv),
            ],
            self.trial_metadata,  # return metadata without updates
        )

    def _participants_csv(self) -> str:
        """Return a CSV of patient-level metadata for the given trial."""
        participants = json_normalize(
            data=self.trial_metadata,
            record_path=["participants"],
            meta=[prism.PROTOCOL_ID_FIELD_NAME],
        )

        participants.drop("samples", axis=1, inplace=True, errors="ignore")

        return participants.to_csv(index=False)

    def _samples_csv(self) -> str:
        """Return a CSV of patient-level metadata for the given trial."""
        samples = json_normalize(
            data=self.trial_metadata,
            record_path=["participants", "samples"],
            meta=[
                prism.PROTOCOL_ID_FIELD_NAME,
                ["participants", "cimac_participant_id"],
            ],
        )

        samples.drop("aliquots", axis=1, inplace=True, errors="ignore")

        return samples.to_csv(index=False)
