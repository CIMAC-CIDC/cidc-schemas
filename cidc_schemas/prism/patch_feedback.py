from typing import List, Union
from collections import Counter, defaultdict
from functools import wraps

from .constants import SUPPORTED_MANIFESTS


def _gen_to_list(f):
    @wraps(f)
    def inner(*a, **kw):
        return list(f(*a, **kw))

    return inner


@_gen_to_list
def manifest_feedback(
    template_type: str, patch: dict, current_md: dict
) -> List[Union[List, str]]:
    """
    Generates user feedback for a template generated patch. At least for now
    it's manifest specific messages on newly created participants, samples, etc. 

    Returns: list of feedback strings (think warnings) or nested list of strings etc.
                Nestedness of lists is for a poor man's formatting in the UI.

    """

    if template_type not in SUPPORTED_MANIFESTS:
        return []

    shipment = patch["shipments"][0]
    trial_id = patch["protocol_identifier"]
    current_pts = {
        p["cimac_participant_id"]: p for p in current_md.get("participants", [])
    }
    participants = {p["cimac_participant_id"]: p for p in patch["participants"]}

    sample_count = sum(len(p["samples"]) for p in participants.values())

    yield (
        f"{sample_count} samples from {len(participants)} participants in "
        f"manifest {shipment['manifest_id']!r} for {trial_id}/{shipment['assay_type']}"
    )

    new_ps_ids = set(participants).difference(current_pts)
    yield _format_new_participants({id: participants[id] for id in new_ps_ids})

    upd_ps_ids = set(participants).intersection(current_pts)

    if upd_ps_ids:
        existing_samples = {
            s["cimac_id"]: dict(s, cimac_participant_id=cpid)
            for cpid, p in current_pts.items()
            for s in p["samples"]
        }

        yield _format_updated_participants(
            {id: participants[id] for id in upd_ps_ids}, existing_samples
        )


def _samples_extra_id(samples, extra_id_name):
    ids = set([s.get(extra_id_name) for s in samples])
    if len(ids) != len(samples):
        if len(ids) == 1:
            return f"Found the same {extra_id_name} {ids.pop()!r} for all {len(samples)} samples"
        else:
            return f"Found only {len(ids)} different {extra_id_name} for {len(samples)} samples"


@_gen_to_list
def _format_new_samples(new_samples):

    s_per_part = Counter([s["cimac_participant_id"] for s in new_samples]).values()
    new_s_per_part_count = min(s_per_part)
    spp_max = max(s_per_part)
    if new_s_per_part_count != spp_max:
        new_s_per_part_count = f"{new_s_per_part_count}-{spp_max}"
    yield f'with {len(new_samples)} new sample{"s" if len(new_samples) > 1 else ""}: {new_s_per_part_count} sample{"s" if spp_max > 1 else ""} per participant'

    psid_warn = _samples_extra_id(new_samples, "parent_sample_id")
    if psid_warn:
        yield psid_warn

    psid_warn = _samples_extra_id(new_samples, "processed_sample_id")
    if psid_warn:
        yield psid_warn

    cc = Counter([s["collection_event_name"] for s in new_samples])
    if len(cc) == 1:
        yield f"collection_event_name event for all {len(new_samples)} - {new_samples[0]['collection_event_name']}"
    else:
        yield f"{len(cc)} collection events"
        yield [f"{count} {tp}'s" for tp, count in cc.items()]


@_gen_to_list
def _format_new_participants(new_ps: list) -> List[Union[List, str]]:
    yield f"adds {len(new_ps)} new participants"

    if new_ps:
        new_samples = [
            dict(s, cimac_participant_id=cpid)
            for cpid, p in new_ps.items()
            for s in p["samples"]
        ]

        new_samples_warn = _format_new_samples(new_samples)
        if new_samples_warn:
            yield new_samples_warn


@_gen_to_list
def _format_updated_participants(
    upd_ps: list, existing_samples: list
) -> List[Union[List, str]]:
    yield f"updates {len(upd_ps)} existing participants"

    new_samples, upd_samples = [], []
    for cpid, p in upd_ps.items():
        for s in p["samples"]:
            s = dict(s, cimac_participant_id=cpid)
            if s["cimac_id"] in existing_samples:
                upd_samples.append(s)
            else:
                new_samples.append(s)

    if new_samples:
        new_samples_warn = _format_new_samples(new_samples)
        if new_samples_warn:
            yield new_samples_warn

    if upd_samples:
        upd_samples_warn = _format_upd_samples(upd_samples)
        if upd_samples_warn:
            yield upd_samples_warn


@_gen_to_list
def _format_upd_samples(upd_samples):
    yield f"with {len(upd_samples)} updated existing sample{'s' if len(upd_samples) > 1 else ''}"

    # #TODO
    # changes_count = 0
    # for s in upd_samples:
    #     e = existing_samples[s["cimac_id"]]
    #     if s != e:
    #         changes_count += 1
    #         print(f'\t\t\tdiff for {s["cimac_id"]}:')
    #         for k in s:
    #             if s[k] != e[k]:
    #                 print(f"\t\t\t\t {k!r} was {e[k]} updated to {s[k]}")
    # print(f"\t\t\tand {len(upd_samples)-changes_count} unchanged")
