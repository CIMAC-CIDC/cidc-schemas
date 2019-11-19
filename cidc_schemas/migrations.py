from copy import deepcopy
from typing import NamedTuple, Dict


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