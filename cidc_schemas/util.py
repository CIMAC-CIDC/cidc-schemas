import json
import yaml
import openpyxl
import os
import re
import jinja2
from typing import Union, BinaryIO, List

JSON = Union[dict, list, str, int, float]

from deepdiff import grep


def load_pipeline_config_template(name: str):
    curdir = os.path.dirname(os.path.abspath(__file__))
    loader = jinja2.FileSystemLoader(curdir)
    return jinja2.Environment(loader=loader).get_template(
        f"pipeline_configs/{name}.yaml.j2"
    )


def participant_id_from_cimac(cimac_id: str) -> str:
    assert len(cimac_id) == len("CTTTPPPSS.00")
    return cimac_id[:7]


def get_all_paths(ct: dict, key: str, dont_throw=False) -> List[str]:
    """
    find all paths to the given key in the dictionary

    Args:
        ct: clinical_trial object to be modified
        key: the identifier we are looking for in the dictionary

    Throws:
        KeyError if *key* is not found within *ct*

    Returns:
        arg1: string describing the location of the key
        in python-ish access style: "root['access']['path'][0]['something']"
    """

    # first look for key as is
    ds1 = ct | grep(key, match_string=True, case_sensitive=True)
    count1 = 0
    if "matched_values" in ds1:
        count1 = len(ds1["matched_values"])

    # the hack fails if both work... probably need to deal with this
    if count1 == 0:
        if dont_throw:
            return []
        else:
            raise KeyError(f"key: {key} not found")

    return ds1["matched_values"]


def get_path(ct: dict, key: str) -> str:

    all_paths = get_all_paths(ct, key)

    return all_paths.pop()


def split_python_style_path(path: str) -> list:
    """
    Will parse `get_path` output (`root['some']['access']['path']`)
    to a list of typed (int/str) tokens

    >>> list(split_python_style_path("root['some']['access']['path']"))
    ['some', 'access', 'path']

    >>> list(split_python_style_path("root['with'][0]['integers'][1]['too']"))
    ['with', 0, 'integers', 1, 'too']

    """

    # strip "root[]"
    assert path.startswith("root[")
    path = path[4:]
    # tokenize
    for groups in re.findall(r"\[(([0-9]*)|'([^\]]+)')\]", path):
        yield groups[2] or int(groups[1])


def get_source(ct: dict, key: str, skip_last=None) -> (JSON, JSON):
    """
    extract the object in the dictionary specified by
    the supplied key (or one of its parents.)

    Args:
        ct: clinical_trial object to be searched
        key: the identifier we are looking for in the dictionary,
        skip_last: how many levels at the end of key path we want to skip.
    Returns:
        arg1: the value present in `ct` at the `key` path
        arg2: extra metadata collected while descending down `key` path
    """

    tokens = list(split_python_style_path(key))

    if skip_last:
        last_idx = -1 * skip_last
        last_token = tokens[last_idx]
        tokens = tokens[0:last_idx]
    else:
        last_token = tokens[-1]

    extra_metadata = {}

    def _update_extra_metadata(token, level, namespace):
        if not isinstance(level, dict):
            return namespace
        # We collect every primitive value present on `level`
        # with keys that aren't the `token` key we are looking for.
        # If we are on the last token, we're at the artifact-specific
        # metadata level, so we collect all values, not just primitives.
        is_artifact_specific = token == last_token
        for k, v in level.items():
            if k != token:
                if is_artifact_specific or isinstance(v, (int, float, str)):
                    prop_name = f"{namespace}.{k}" if namespace else k
                    extra_metadata[prop_name] = v
        return f"{namespace}.{token}" if namespace else token

    # Iteratively follow the key path down into the dictionary
    cur_obj = ct
    namespace = ""
    for token in tokens:
        namespace = _update_extra_metadata(token, cur_obj, namespace)
        cur_obj = cur_obj[token]

    # Extract extra_metadata from the last level if it was skipped
    if skip_last:
        _update_extra_metadata(last_token, cur_obj, namespace)

    return cur_obj, extra_metadata
