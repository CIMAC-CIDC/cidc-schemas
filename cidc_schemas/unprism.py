from pandas.io.json import json_normalize

from .prism import PROTOCOL_ID_FIELD_NAME

def unprism_participants(trial_metadata: dict):
    """Return a CSV of patient-level metadata for the given trial."""
    participants = json_normalize(data=trial_metadata, record_path=['participants'],
                                  meta=[PROTOCOL_ID_FIELD_NAME])

    participants.drop('samples', axis=1, inplace=True, errors='ignore')

    return participants.to_csv(index=False)


def unprism_samples(assay_type: str):
    """Return a CSV of patient-level metadata for the given trial."""
    samples = json_normalize(data=assay_type, record_path=['participants', "samples"],
                             meta=[PROTOCOL_ID_FIELD_NAME, ["participants", "cimac_participant_id"]])

    samples.drop('aliquots', axis=1, inplace=True, errors='ignore')

    return samples.to_csv(index=False)
