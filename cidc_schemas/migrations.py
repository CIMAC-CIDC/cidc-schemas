from copy import deepcopy
from typing import NamedTuple, Dict

from .prism.core import _ENCRYPTED_FIELD_LEN, _encrypt


def _follow_path(d: dict, *keys):
    for key in keys:
        try:
            d = d[key]
        except (KeyError, IndexError):
            return None
    return d


class MigrationError(Exception):
    pass


class MigrationResult(NamedTuple):
    result: dict
    file_updates: Dict[str, dict]


class migration:
    """
    A `migration` contains two static methods for transforming
    JSON trial metadata: `upgrade` and `downgrade`. Each returns takes
    a JSON trial metadata blob as its first argument, and returns a `MigrationResult`.
    `upgrade` and `downgrade` are inverses, i.e., for given `metadata`:
        >>> upgraded = migration.upgrade(metadata)
        >>> downgraded = migration.downgrade(upgraded.result)
        >>> metadata == downgraded # should be True
    """

    @staticmethod
    def upgrade(metadata: dict, *args, **kwargs) -> MigrationResult:
        raise NotImplementedError

    @staticmethod
    def downgrade(metadata: dict, *args, **kwargs) -> MigrationResult:
        raise NotImplementedError


class v0_23_18_to_v0_24_0(migration):
    """
    Restructure the Olink data model, introducing the concept of batches representing
    each new upload. Trials can now have both an optional study-level combined file
    *and* batch-level combined files.
    """

    @classmethod
    def upgrade(cls, metadata: dict, *args, **kwargs) -> MigrationResult:
        if "assays" not in metadata or "olink" not in metadata["assays"]:
            return MigrationResult(metadata, {})

        file_updates = {}
        batch_id = "1"
        olink = metadata["assays"]["olink"]

        # Add a batch_id to the record file URLs
        for record in olink["records"]:
            files = record["files"]
            for f in [files["assay_npx"], files["assay_raw_ct"]]:
                if "object_url" in f:
                    object_url = f["object_url"]
                    f["object_url"] = object_url.replace(
                        "chip_", f"batch_{batch_id}/chip_"
                    )
                    file_updates[object_url] = f

        olink["batch_id"] = batch_id
        new_olink = {"batches": [olink]}
        if "study" in olink:
            new_olink["study"] = olink.pop("study")
            new_olink["study"]["npx_file"] = new_olink["study"].pop("study_npx")

        metadata["assays"]["olink"] = new_olink

        return MigrationResult(metadata, file_updates)

    @classmethod
    def downgrade(cls, metadata: dict, *args, **kwargs) -> MigrationResult:
        """
        NOTE: downgrades are not possible on this breaking change. Downgrading 
        would require making arbitrary decisions about which data to delete and 
        which to keep.
        """
        return MigrationResult(metadata, {})


class v0_23_0_to_v0_23_1(migration):
    """
    renaming 'arbitrary_trial_specific_clinical_annotations' to 'clinical'
    """

    @classmethod
    def upgrade(cls, metadata: dict, *args, **kwargs) -> MigrationResult:
        if "rnaseq_analysis" in metadata.get("analysis", {}):
            metadata["analysis"]["rna_analysis"] = metadata["analysis"].pop(
                "rnaseq_analysis"
            )
        for p in metadata.get("participants", []):
            if "arbitrary_trial_specific_clinical_annotations" in p:
                p["clinical"] = p.pop("arbitrary_trial_specific_clinical_annotations")

        return MigrationResult(metadata, {})

    @classmethod
    def downgrade(cls, metadata: dict, *args, **kwargs) -> MigrationResult:
        if "rna_analysis" in metadata.get("analysis", {}):
            metadata["analysis"]["rnaseq_analysis"] = metadata["analysis"].pop(
                "rna_analysis"
            )

        for p in metadata.get("participants", []):
            if "clinical" in p:
                p["arbitrary_trial_specific_clinical_annotations"] = p.pop("clinical")

        return MigrationResult(metadata, {})


class v0_21_1_to_v0_22_0(migration):
    """
    Hashing participant/participant_id and sample/parent_sample_id,processed_sample_id
    """

    @classmethod
    def upgrade(cls, metadata: dict, *args, **kwargs) -> MigrationResult:

        not_reported = _encrypt("Not reported")

        for p in metadata.get("participants", []):

            if (
                "participant_id" in p
                and len(p["participant_id"]) != _ENCRYPTED_FIELD_LEN
            ):
                p["participant_id"] = _encrypt(p["participant_id"])

            for s in p.get("samples", []):

                if s.get("parent_sample_id") == "X":
                    s["parent_sample_id"] = s["processed_sample_id"]

                if (
                    "processed_sample_id" not in s
                    or s["processed_sample_id"] == not_reported
                ):
                    s["processed_sample_id"] = s["parent_sample_id"]

                if (
                    len(s.get("parent_sample_id", "")) == _ENCRYPTED_FIELD_LEN
                    and len(s.get("processed_sample_id", "")) == _ENCRYPTED_FIELD_LEN
                ):
                    # both are hashed so skip
                    continue

                if "processed_sample_id" in s:
                    s["processed_sample_id"] = _encrypt(s["processed_sample_id"])
                if "parent_sample_id" in s:
                    s["parent_sample_id"] = _encrypt(s["parent_sample_id"])

        return MigrationResult(metadata, {})

    @classmethod
    def downgrade(cls, metadata: dict, *args, **kwargs):
        MigrationResult(metadata, {})


class v0_15_2_to_v0_15_3(migration):
    """
    v0.15.2: allowed_cohort_names included "Not reported" as an allowed value.
    v0.15.3: allowed_cohort_names was updated to use "Not_reported" instead of "Not reported" for this value.
    """

    @classmethod
    def upgrade(cls, metadata: dict, *args, **kwargs) -> MigrationResult:
        for p in metadata.get("participants", []):
            if p["cohort_name"] == "Not reported":
                p["cohort_name"] = "Not_reported"

        return MigrationResult(metadata, {})

    @classmethod
    def downgrade(cls, metadata: dict, *args, **kwargs):
        for p in metadata.get("participants", []):
            if p["cohort_name"] == "Not_reported":
                p["cohort_name"] == "Not reported"

        return MigrationResult(metadata, {})


class v0_10_2_to_v0_11_0(migration):
    """
    v0.11.0 allowed_cohort_names and allowed_collection_event_names were
    introduced as required fields in clinical_trial.json.
    They are designed to impose further enum constraints on participant/cohort_name
    and sample/collection_event_name correspondingly.
    """

    @classmethod
    def upgrade(cls, metadata: dict, *args, **kwargs) -> MigrationResult:
        cohorts = set(metadata.get("allowed_cohort_names", []))
        collection_names = set(metadata.get("allowed_collection_event_names", []))

        for p in metadata.get("participants", []):
            cohorts.add(p["cohort_name"])

            for s in p.get("samples", []):
                collection_names.add(s["collection_event_name"])

        return MigrationResult(
            dict(
                metadata,
                allowed_cohort_names=list(cohorts),
                allowed_collection_event_names=list(collection_names),
            ),
            {},
        )

    @classmethod
    def downgrade(cls, metadata: dict, *args, **kwargs) -> MigrationResult:

        metadata.pop("allowed_cohort_names")
        metadata.pop("allowed_collection_event_names")

        return MigrationResult(metadata, {})


class v0_10_0_to_v0_10_2(migration):
    """
    v0.10.0 and previous wrongly treat assay_raw_ct files as XLSX.
    This issue was fixed in v0.10.1, and this migrations module was added
    in v0.10.2.
    """

    @staticmethod
    def _convert(metadata: dict, to_csv: bool) -> MigrationResult:
        """Either convert assay_raw_ct's data format from XLSX to CSV or vice versa."""
        target_format = "CSV" if to_csv else "XLSX"
        target_ext = ".csv" if to_csv else ".xlsx"
        current_ext = ".xlsx" if to_csv else ".csv"

        updated_metadata = deepcopy(metadata)

        # Extract the olink records
        olink_records = _follow_path(updated_metadata, "assays", "olink", "records")

        # If there are no olink_records, we have no changes to make
        if not olink_records:
            return MigrationResult(updated_metadata, {})

        # Otherwise, we need to look for every assay_raw_ct artifact,
        # extract its GCS info, and update its data format
        file_updates = {}
        for record in olink_records:
            # Extract artifact record
            assay_raw_ct = _follow_path(record, "files", "assay_raw_ct")

            if not assay_raw_ct:
                raise MigrationError(f"Olink record has unexpected structure: {record}")

            # Update the data_format
            assay_raw_ct["data_format"] = target_format

            # Update the object_url and track this update in the file_updates dict
            old_object_url = assay_raw_ct["object_url"]
            new_object_url = old_object_url.rstrip(current_ext) + target_ext
            assay_raw_ct["object_url"] = new_object_url
            file_updates[old_object_url] = assay_raw_ct

        return MigrationResult(updated_metadata, file_updates)

    @classmethod
    def upgrade(cls, metadata: dict, *args, **kwargs) -> MigrationResult:
        return cls._convert(metadata, to_csv=True)

    @classmethod
    def downgrade(cls, metadata: dict, *args, **kwargs) -> MigrationResult:
        return cls._convert(metadata, to_csv=False)
