import os
from copy import deepcopy
from typing import NamedTuple, Tuple, Optional, List, Dict, Union

from cidc_schemas.template import Template
from cidc_schemas.template_reader import XlTemplateReader
from cidc_schemas.util import participant_id_from_cimac
from cidc_schemas.json_validation import load_and_validate_schema
from cidc_schemas.prism import LocalFileUploadEntry, PROTOCOL_ID_FIELD_NAME

from ...constants import TEMPLATE_EXAMPLES_DIR


class PrismTestData(NamedTuple):
    upload_type: str
    prismify_args: Tuple[XlTemplateReader, Template]
    prismify_patch: dict
    upload_entries: List[LocalFileUploadEntry]

    base_trial: dict
    target_trial: dict


def get_prismify_args(upload_type) -> Tuple[XlTemplateReader, Template]:
    xlsx_path = os.path.join(TEMPLATE_EXAMPLES_DIR, f"{upload_type}_template.xlsx")
    reader, errs = XlTemplateReader.from_excel(xlsx_path)
    assert len(errs) == 0, f"Failed to load template reader for {upload_type}"
    template = Template.from_type(upload_type)
    return (reader, template)


def get_test_trial(
    cimac_ids: Optional[List[str]] = None,
    assays: Optional[dict] = None,
    analysis: Optional[dict] = None,
    allowed_collection_event_names=["Not_reported"],
    allowed_cohort_names=["Not_reported"],
):
    """
    Build a test trial metadata object. `cimac_ids` is a list of CIMAC IDs to include in
    the `participants` portion of the metadata.
    """
    cimac_ids = cimac_ids or []
    participants: Dict[str, dict] = {}
    for cimac_id in cimac_ids:
        participant_id = participant_id_from_cimac(cimac_id)
        if participant_id not in participants:
            participants[participant_id] = {
                "cimac_participant_id": participant_id,
                "cohort_name": "Not_reported",
                "participant_id": "",
                "samples": [],
            }
        sample = {
            "cimac_id": cimac_id,
            "collection_event_name": "Not_reported",
            "parent_sample_id": "",
            "sample_location": "",
            "type_of_sample": "Not Reported",
        }
        participants[participant_id]["samples"].append(sample)

    trial = {
        PROTOCOL_ID_FIELD_NAME: "test_prism_trial_id",
        "allowed_cohort_names": allowed_cohort_names,
        "allowed_collection_event_names": allowed_collection_event_names,
    }
    trial["participants"] = list(participants.values())

    if assays:
        trial["assays"] = assays
    if analysis:
        trial["analysis"] = analysis

    # Ensure we're producing a valid trial
    validator = load_and_validate_schema("clinical_trial.json", return_validator=True)
    validator.validate(trial)

    return trial


def copy_dict_with_branch(base: dict, patch: dict, branch: Union[str, List[str]]):
    if isinstance(branch, str):
        branch = [branch]

    target = deepcopy(base)

    for key in branch:
        assert key in patch, f"`patch` must have key {key}"
        target[key] = deepcopy(patch[key])

    return target
