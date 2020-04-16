from typing import List, Union
from collections import Counter, defaultdict

from .constants import SUPPORTED_MANIFESTS


def _samples_extra_id(samples, extra_id_name):
    ids = set([s.get(extra_id_name) for s in samples])
    if ids.difference([None]):  # if we have some values for this id prop at all
        if len(ids) != len(samples):
            if len(ids) == 1:
                return f"Found the same {extra_id_name} {ids.pop()!r} for all {len(samples)} samples"
            else:
                return f"Found only {len(ids)} different {extra_id_name} for {len(samples)} samples"


def format_new_samples(new_samples):

    spp = Counter([s["cimac_participant_id"] for s in new_samples])
    spp_min = min(spp.values())
    spp_max = max(spp.values())
    if spp_min != spp_max:
        spp = f"{spp_min}-{spp_max}"
    else:
        spp = spp_min
    yield f'with {len(new_samples)} new samples: {spp} sample{"s" if spp_max > 1 else ""} per participant'

    psid_warn = _samples_extra_id(new_samples, "parent_sample_id")
    if psid_warn:
        yield psid_warn

    psid_warn = _samples_extra_id(new_samples, "processed_sample_id")
    if psid_warn:
        yield psid_warn

    cc = Counter([s["collection_event_name"] for s in new_samples]).items()
    if len(cc) == 1:
        yield f"Collection event for all {len(new_samples)} - {new_samples[0]['collection_event_name']}"
    else:
        yield f"{len(cc)} collection events"
        yield [f"{count} {tp}'s" for tp, count in cc]


def patch_feedback(
    template_type: str, patch: dict, current_md: dict
) -> List[Union[List, str]]:
    """
    Generates user feedback for a template generated patch. At least for now
    it's manifest specific messages on newly created participants, samples, etc. 

    Returns: list of feedback strings (think warnings) or nested list of strings etc.
                Nestedness of lists is for a poor man's formatting in the UI.

    """

    res = []
    if template_type in SUPPORTED_MANIFESTS:

        shipment = patch["shipments"][0]
        trial_id = patch["protocol_identifier"]
        participants = {p["cimac_participant_id"]: p for p in patch["participants"]}
        samples = [dict(s, **p) for p in participants.values() for s in p["samples"]]

        res.append(
            f"{len(samples)} samples from {len(participants)} participants in "
            f"manifest {shipment['manifest_id']!r} for {trial_id}/{shipment['assay_type']}"
        )

        new_ps = set(participants).difference(current_md)

        new_ps_clause = [f"adds {len(new_ps)} new participants"]
        res.append(new_ps_clause)

        if new_ps:
            new_samples = [
                dict(s, **p)
                for cpid, p in participants.items()
                for s in p["samples"]
                if cpid in new_ps
            ]

            new_ps_clause.append([out for out in format_new_samples(new_samples)])

        upd_ps = set(participants).intersection(current_md)
        if upd_ps:
            upd_ps_clause = [f"updates {len(upd_ps)} existing participants"]
            res.append(upd_ps_clause)

            existing_samples = {
                s["cimac_id"]: dict(s, **p)
                for p in current_md.values()
                for s in p["samples"]
            }

            new_samples, upd_samples = [], []
            for cpid in upd_ps:
                p = participants[cpid]

                existing_samples = []
                for s in p["samples"]:
                    s = dict(s, **p)
                    if s["cimac_id"] in existing_samples:
                        upd_samples.append(s)
                    else:
                        new_samples.append(s)

            if new_samples:
                upd_ps_clause.append([out for out in format_new_samples(new_samples)])

            if upd_samples:
                upd_ps_clause.append(
                    f"with {len(upd_samples)} updated existing samples"
                )
                # TODO

    return res
