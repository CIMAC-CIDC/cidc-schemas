"""Merge CIDC schemas metadata dictionaries."""

import re
import logging
from typing import BinaryIO, List, NamedTuple, Optional, Callable

import openpyxl
import jsonschema
from jsonmerge import Merger, strategies

from ..json_validation import load_and_validate_schema, _Validator
from ..util import get_path, get_source
from .extra_metadata import EXTRA_METADATA_PARSERS
from .constants import PROTOCOL_ID_FIELD_NAME

logger = logging.getLogger(__file__)


def _set_data_format(ct: dict, artifact: dict):
    """
    Discover the correct data format for the given artifact.
    Args:
        ct: a clinical trial object with artifact inserted
        artifact: a reference to the artifact object inserted in `ct`.
        NOTE: in-place updates to artifact must trigger in-place updates to `ct`.
    """
    # This is invalid for all artifact types, and will
    # deliberately trigger a validation error below.
    artifact["data_format"] = "[NOT SET]"

    validator: jsonschema.Draft7Validator = load_and_validate_schema(
        "clinical_trial.json", return_validator=True
    )

    for error in validator.iter_errors(ct):
        if not isinstance(error, jsonschema.exceptions.ValidationError):
            continue

        if error.validator != "const":
            continue

        if error.path[-1] != "data_format":
            continue

        if error.instance != artifact["data_format"]:
            continue

        # Since data_format is specified as a constant in the schema,
        # the validator_value on this exception will be the desired data format.
        artifact["data_format"] = error.validator_value
        return

    # data format was not set!


def _get_uuid_info(ct: dict, artifact_uuid: str) -> (dict, dict):
    """
        Using uuid to find path in CT where corresponding artifact is located.
    """
    uuid_field_path = get_path(ct, artifact_uuid)

    # As "uuid_field_path" contains path to a field with uuid,
    # we're looking for an artifact that contains it, not the "string" field itself
    # That's why we need skip_last=1, to get 1 "level" higher
    # from 'uuid_field_path' field to it's parent - existing_artifact obj
    return get_source(ct, uuid_field_path, skip_last=1)


def merge_artifact(
    ct: dict,
    artifact_uuid: str,
    object_url: str,
    assay_type: str,
    file_size_bytes: int,
    uploaded_timestamp: str,
    crc32c_hash: Optional[str] = None,
    md5_hash: Optional[str] = None,
) -> (dict, dict, dict):
    """
    create and merge an artifact into the metadata blob
    for a clinical trial. The merging process is automatically
    determined by inspecting the gs url path.
    Args:
        ct: clinical_trial object to be searched
        artifact_uuid: artifact identifier
        object_url: the gs url pointing to the object being added
        file_size_bytes: integer specifying the number of bytes in the file
        uploaded_timestamp: time stamp associated with this object
        md5_hash: md5 hash of the uploaded object, provided by GCS for non-composite objects
        crc32c_hash: crc32c hash of the uploaded object, provided by GCS for all objects
    Returns:
        ct: updated clinical trial object
        artifact: updated artifactf
        additional_artifact_metadata: relevant metadata collected while updating artifact
    """
    assert (
        crc32c_hash or md5_hash
    ), f"Either crc32c_hash or md5_hash must be provided for artifact: {object_url}"

    # urls are created like this in _process_property:
    file_name, uuid = object_url.split("/")[-2:]

    artifact_patch = {
        # TODO 1. this artifact_category should be filled out during prismify
        "artifact_category": "Assay Artifact from CIMAC",
        "object_url": object_url,
        "file_name": file_name,
        "file_size_bytes": file_size_bytes,
        "uploaded_timestamp": uploaded_timestamp,
    }

    if crc32c_hash:
        artifact_patch["crc32c_hash"] = crc32c_hash
    if md5_hash:
        artifact_patch["md5_hash"] = md5_hash

    return _update_artifact(ct, artifact_patch, artifact_uuid)


class InvalidMergeTargetException(ValueError):
    """Exception raised for target of merge_clinical_trial_metadata being non schema compliant."""


def merge_artifact_extra_metadata(
    ct: dict, artifact_uuid: str, assay_hint: str, extra_metadata_file: BinaryIO
) -> (dict, dict, dict):
    """
    Merges parsed extra metadata returned by extra_metadata_parsing to
    corresponding artifact objects within the patch.
    Args:
        ct: preliminary patch from upload_assay
        artifact_uuid: passed from upload assay
        assay_hint: assay type
        extra_metadata_file: extra metadata file in BinaryIO
    Returns:
        ct: updated clinical trial object
        artifact: updated artifact
        additional_artifact_metadata: relevant metadata collected while updating artifact
    """

    if assay_hint not in EXTRA_METADATA_PARSERS:
        raise Exception(f"Assay {assay_hint} does not support extra metadata parsing")
    extract_metadata = EXTRA_METADATA_PARSERS[assay_hint]

    artifact_extra_md_patch = extract_metadata(extra_metadata_file)
    return _update_artifact(ct, artifact_extra_md_patch, artifact_uuid)


def _update_artifact(
    ct: dict, artifact_patch: dict, artifact_uuid: str
) -> (dict, dict, dict):
    """ Updates the artifact with uuid `artifact_uuid` in `ct`,
    and return the updated clinical trial and artifact objects
    Args:
        ct: clinical trial object
        artifact_patch: artifact object patch
        artifact_uuid: artifact identifier
    Returns:
        ct: updated clinical trial object
        artifact: updated artifact
        additional_artifact_metadata: relevant metadata collected while updating artifact
    """

    artifact, additional_artifact_metadata = _get_uuid_info(ct, artifact_uuid)

    # TODO this might be better with merger:
    # artifact_schema = load_and_validate_schema(f"artifacts/{artifact_type}.json")
    # artifact_parent[file_name] = Merger(artifact_schema).merge(existing_artifact, artifact)
    artifact.update(artifact_patch)

    _set_data_format(ct, artifact)

    # return the artifact that was merged and the new object
    return ct, artifact, additional_artifact_metadata


class MergeCollisionException(ValueError):
    def __init__(self, prop_name, base_val, head_val, context=None):
        self.prop_name = prop_name
        self.base_val = base_val
        self.head_val = head_val
        self.context = context or dict()

    def __str__(self):
        res = f"Detected mismatch of {self.prop_name}={self.base_val!r} and {self.prop_name}={self.head_val!r}"
        if self.context:
            res += " in " + " ".join(f"{k}={v!r}" for k, v in self.context.items())
        return res

    def with_context(self, **add_context):
        return MergeCollisionException(
            self.prop_name,
            self.base_val,
            self.head_val,
            dict(self.context, **add_context),
        )


class ThrowOnOverwrite(strategies.Strategy):
    """
    Similar to the jsonmerge's built in 'discard' strategy,
    but throws an error if the value already exists. This is
    used to prevent updates in `merge_clinical_trial_metadata`.
    """

    def merge(self, walk, base, head, schema, meta, **kwargs):
        if base.is_undef():
            return head
        if base.val != head.val:
            prop_name = base.ref.rsplit("/", 1)[-1]
            raise MergeCollisionException(prop_name, base.val, head.val)
        return base

    def get_schema(self, walk, schema, **kwargs):
        return schema


class ObjectContextForMergeCollisionException(MergeCollisionException):
    """ Used for providing full object context (not only field level collision)
        for parent ArrayMergeById strategy """

    def __init__(self, merge_collision, object_context):
        self.merge_collision = merge_collision
        self.object_context = object_context

    def __str__(self):
        # delegating to MergeCollisionException
        return str(self.merge_collision)

    def with_context(self, **add_context):
        # delegating to MergeCollisionException
        return ObjectContextForMergeCollisionException(
            self.merge_collision.with_context(**add_context), self.object_context
        )


class ObjectMergeWithContextForMergeCollision(strategies.ObjectMerge):
    def merge(self, walk, base, head, schema, meta, **kwargs):
        try:
            return super().merge(walk, base, head, schema, meta, **kwargs)
        except MergeCollisionException as e:
            # Swaping base and head in exception for current objects'
            # so in the parent container/array we will have context of current object
            # and not context of only one property of this object
            raise ObjectContextForMergeCollisionException(e, head)
            # Passes `head` as context, but might as well pass `base`,
            # as the intended use it to do `.get_key(walk, head|base, idRef)
            # in the parent ArrayMergeById strategy


class ArrayMergeByIdWithContextForMergeCollision(strategies.ArrayMergeById):
    def merge(self, walk, base, head, schema, meta, idRef="id", **kwargs):
        try:
            return super().merge(walk, base, head, schema, meta, idRef=idRef, **kwargs)
        except ObjectContextForMergeCollisionException as e:
            try:
                # Adding context from MergeById
                ctx_val = self.get_key(walk, e.object_context, idRef)
                ctx_key = idRef.split("/")[-1]
                raise e.merge_collision.with_context(**{ctx_key: ctx_val})
            except jsonschema.exceptions.RefResolutionError:
                # self.get_key failed, nothing to do but re-raise MergeCollision as is
                raise e.merge_collision


PRISM_MERGE_STRATEGIES = {
    # This overwrites the default jsonmerge merge strategy for literal values.
    "overwrite": ThrowOnOverwrite(),
    # This adds context to MergeCollisions
    "arrayMergeById": ArrayMergeByIdWithContextForMergeCollision(),
    "objectMerge": ObjectMergeWithContextForMergeCollision(),
    # Alias the builtin jsonmerge overwrite strategy
    "overwriteAny": strategies.Overwrite(),
}


def merge_clinical_trial_metadata(patch: dict, target: dict) -> (dict, List[str]):
    """
    Merges two clinical trial metadata objects together
    Args:
        patch: the metadata object to add
        target: the existing metadata object
    Returns:
        arg1: the merged metadata object
        arg2: list of validation errors
    """

    validator: _Validator = load_and_validate_schema(
        "clinical_trial.json", return_validator=True
    )

    # first we assert original object is valid
    try:
        validator.validate(target)
    except jsonschema.ValidationError as e:
        raise InvalidMergeTargetException(
            f"Merge target is invalid: {target}\n{e}"
        ) from e

    # assert the un-mutable fields are equal
    # these fields are required in the schema
    # so previous validation assert they exist
    if patch.get(PROTOCOL_ID_FIELD_NAME) != target.get(PROTOCOL_ID_FIELD_NAME):
        raise InvalidMergeTargetException(
            "Unable to merge trials with different " + PROTOCOL_ID_FIELD_NAME
        )

    # merge the two documents
    merger = Merger(validator.schema, strategies=PRISM_MERGE_STRATEGIES)
    merged = merger.merge(target, patch)

    return merged, list(validator.iter_error_messages(merged))
