import os
import jsonschema
from typing import Any, Dict, Iterable, List, Set, Tuple

from cidc_schemas.constants import SCHEMA_DIR
from cidc_schemas.json_validation import _load_dont_validate_schema


SCHEMA_STORE: Dict[Tuple[str, bool], dict] = dict()


def add_merge_pointer_to_data_store(
    root: dict, merge_pointer: str, data_store: dict
) -> Set[str]:
    """
    Updates data by nested-setting the endpoint of the pointer with the part of the schema it points to
    The definition's "required" is a boolean based on the last step

    Parameters
    ----------
    root: dict
        a jsonschemas definition
    merge_pointer: str
        the merge_pointer to fish out of root with descend_dict()
    data_store: dict
        the nested dict to put the referenced definition
        set via nested_set() which adds in place

    Returns
    -------
    required: Set[str] = set()
        the list of property names that are required
    """
    required: Set[str] = set()

    # break up the merge pointer into a set of keys
    # remove any array parts -- we'll always keep descending
    levels: List[str] = [
        part
        for part in merge_pointer.split("/")
        if not part.isdigit() and part not in ("-", "")
    ]
    # want to add back {"items": True} to anything that's a array
    ptr: int = 0
    array_pointers: List[List[str]] = []
    for part in merge_pointer.split("/"):
        if levels[ptr] == part:
            # there wasn't an array here we dropped
            ptr += 1
            # bail at the end, it'll inherit {"type": "array"}
            if ptr == len(levels):
                break
        else:
            # note the processed pointer up until this point
            array_pointers.append(levels[:ptr])

    root, new_required = descend_dict(root, levels)
    required.update(new_required)

    # if merge_pointer points to a new item in the list
    # make sure we're all the way down and have a description
    if merge_pointer.endswith("-"):
        # updates in place
        load_subschema_from_url(root)
        required.update(root.get("required", []))

        if "properties" in root:
            root = root["properties"]
            required.update(root.get("required", []))
        if root.get("type", "") == "array" and "description" not in root:
            root["description"] = root["items"].get("description", "")

    # update in place instead of returning
    nested_set(data_store, levels, root)

    # for every intermediate array found before add {"items": True}
    # so the template knows this is an array and not an object
    for pointer_to_array in array_pointers:
        # unneeded at the top level since docs are for a singular upload
        if len(pointer_to_array):
            nested_set(data_store, pointer_to_array + ["items"], True)

    return required


def descend_dict(root: dict, levels: List[str]) -> dict:
    """
    Follows `levels` down through `root`
        handles "items", "properties", and "url"s
    Returns the final definition
        "required" is added as a boolean based on the last step

    Parameters
    ----------
    root: dict
        the nested dict schema to traverse
    levels: List[str]
        a series of dict keys

    Returns
    -------
    dict
        the final definition
    required: Set[str]
        a concentated list of "required" across all layers
    """

    def _all_the_way_down(root: dict) -> bool:
        return (
            "items" not in root
            and "properties" not in root
            and (
                # see _handle_url()
                "url" not in root
                or "type" in root
                or "artifacts" in root["url"]
            )
        )

    # traverse the schema using the keys
    required: Set[str] = set()
    for level in levels:
        # keep going while we can
        root = root[level]
        required.update(root.get("required", []))
        # descend into any items, properties, or non-artifact urls
        # single carve out for cytof source_fcs
        while not _all_the_way_down(root) and level != "source_fcs":
            if "items" in root:
                root = root["items"]
                required.update(root.get("required", []))
            if "properties" in root and root["properties"]:
                root = root["properties"]
                required.update(root.get("required", []))
            # updates in place
            load_subschema_from_url(root)
            required.update(root.get("required", []))
            if "items" in root:
                root = root["items"]
                required.update(root.get("required", []))
            if "properties" in root:
                root = root["properties"]
                required.update(root.get("required", []))

    return root, required


def flatten_allOf(schema: dict) -> dict:
    """
    Combines `properties` and `required` inplace across all `allOf` if they exist

    Parameters
    ----------
    schema: dict
        a schema definition that may contain jsonschemas allOf

    Returns
    -------
    schema: dict
        input after update
    """
    if not "properties" in schema:
        schema["properties"] = {}
    if not "required" in schema:
        schema["required"] = []

    # use while in case of allOf > allOf
    while "allOf" in schema:
        for other_schema in schema.pop("allOf"):
            if "properties" in other_schema:
                schema["properties"].update(other_schema["properties"])
            if "required" in other_schema:
                schema["required"].extend(other_schema["required"])
            if "allOf" in other_schema:
                schema["allOf"] = other_schema["allOf"]

    return schema


def get_translated_merge_pointers(context: str, definition: dict) -> Set[str]:
    """
    Get the set of translated merge pointers from a preamble_rows or data_columns definition
    Also handles process_as, and so can return many merge pointers

    Parameters
    ----------
    context: str
        absolute pointer to the location of `definition`
        from which merge_pointers are considered relative
    definition: dict
        a preamble row or data column definition
        can contain merge_pointer and/or process_as

    Returns
    -------
    translated_merge_pointers: Set[str]
        translated absolute merge_pointers from `definition`
    """
    translated_merge_pointers = set()
    if "merge_pointer" in definition:
        translated_merge_pointers.add(translate_merge_pointer(context, definition))
    if "process_as" in definition:
        for process in definition["process_as"]:
            translated_merge_pointers.add(translate_merge_pointer(context, process))

    return translated_merge_pointers


def load_schema(root: str, path: str, as_html: bool = True) -> dict:
    """
    Loads the schema from the given `path` in `root`

    Parameters
    ----------
    root: str
        the folder which contains the schema
    path: str
        the schema to load
    as_html: bool = True
        whether or to convert urls to .html instead of .json
    """
    schema_path = os.path.join(root, path)
    if (schema_path, as_html) in SCHEMA_STORE:
        return SCHEMA_STORE[(schema_path, as_html)]

    # if not converting, just return it straight away
    if not as_html:
        # when loading, always in reference to base dir
        ret = flatten_allOf(_load_dont_validate_schema(schema_path, SCHEMA_DIR))
        SCHEMA_STORE[(schema_path, as_html)] = ret
        return ret

    # otherwise we need to make some url changes
    def _json_to_html(ref: str) -> dict:
        """Update refs to refer to the URL of the corresponding documentation."""
        url = ref.replace(".json", ".html")
        url = url.replace("properties/", "")
        url = url.replace("definitions/", "")
        url = url.replace("/", ".")
        with resolver.resolving(ref) as resolved:
            description = resolved.get("description", "")

        return {"url": url, "description": description}

    # when loading or resolving, always in reference to base dir
    full_json = _load_dont_validate_schema(schema_path, SCHEMA_DIR)
    resolver = jsonschema.RefResolver(f"file://{SCHEMA_DIR}/schemas", full_json)

    # when loading, always in reference to base dir
    ret = flatten_allOf(
        _load_dont_validate_schema(schema_path, SCHEMA_DIR, on_refs=_json_to_html)
    )
    SCHEMA_STORE[(schema_path, as_html)] = ret
    return ret


def load_schemas_in_directory(
    schema_dir: str = SCHEMA_DIR,
    recursive: bool = True,
) -> Dict[str, Dict[str, dict]]:
    """
    Load all JSON schemas into a dictionary keyed on the
    schema directory. Values are dictionaries mapping entity
    names to loaded and validated entity schemas.
    If recursive, goes through all subdirectories as well
    Does not provide as_html, therefore defaults to True
    """
    schemas = {}
    for root, _, paths in os.walk(schema_dir):
        root_schemas = {}
        for path in paths:
            if not path.endswith(".json"):
                continue

            schema_name = path[:-5].replace("/", ".")
            root_schemas[schema_name] = load_schema(root, path)

        if len(root_schemas):
            relative_root = root.replace(schema_dir, "").replace("/", ".")
            relative_root = relative_root.replace(".", "", 1)
            schemas[relative_root] = root_schemas

        if not recursive:
            break

    return schemas


def load_subschema_from_url(definition: dict) -> dict:
    """
    Handles urls in loading the subschema and default descriptions
    Any non-artifact urls are replaced with their corresponding definition
    Does NOT translate artifact urls, as they should be linked

    Parameters
    ----------
    definition: dict
        a jsonschemas definition that may contain "url"

    Returns
    -------
    definition: dict
        input after update
    """
    # handle any level urls
    while (
        "type" not in definition
        and "url" in definition
        and "artifacts" not in definition["url"]
    ):
        schema_path = (
            definition["url"].replace(".", "/").replace("/html", ".json").split("#")[0]
        )
        merge_pointer = (
            definition["url"].split("#")[-1] if definition["url"].count("#") else ""
        )
        schema = load_schema(SCHEMA_DIR, schema_path)

        # save the highest description to use
        description: str = definition.get("description", "")
        # definitions first because properties can point here
        if merge_pointer in schema.get("definitions", {}):
            definition.update(schema["definitions"][merge_pointer])
        elif merge_pointer in schema.get("properties", {}):
            definition.update(schema["properties"][merge_pointer])
        elif merge_pointer == "":
            definition.update(schema)

        # include any lower ones too
        # eg ihc > antibody > antibody
        if "properties" in definition:
            definition["properties"] = {
                k: load_subschema_from_url(v) if isinstance(v, dict) else v
                for k, v in definition["properties"].items()
            }

        if description:
            definition["description"] = description

    # if not elif as url can be an array itself
    if definition.get("type") == "array":
        if "description" not in definition:
            definition["description"] = definition["items"].get("description", "")
        definition["items"] = load_subschema_from_url(definition["items"])

    return definition


def nested_set(dic: dict, keys: Iterable[str], value: Any) -> None:
    """
    Sets a value deep in a dict given a set of keys

    Parameters
    ----------
    dict: dict
        the root dict in which to set a value
    keys: Iterable[str]
        a set of keys representing nested dict levels
    value: Any
        the value to set the bottommost entry to
    """
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def translate_merge_pointer(context_pointer: str, definition: dict) -> str:
    """
    Get the merge_pointer from the definition and combine it with the context
    Handles going up levels if (relative) merge_pointer in definition[0] is nonzero digit

    Parameters
    ----------
    context_pointer: str
        absolute pointer to the location of `definition`
        from which merge_pointers are considered relative
    definition: dict
        a preamble row or data column definition
        must contain merge_pointer

    Returns
    -------
    translated_merge_pointer: str
        the final combined absolute merge_pointer
        will not start with '/'
    """
    context_pointer: str = context_pointer.rstrip("-").lstrip("0/").replace("#", "")
    merge_pointer: str = definition["merge_pointer"]
    if merge_pointer[0].isdigit() and int(merge_pointer[0]):
        context_pointer = "/".join(
            context_pointer.split("/")[: -int(merge_pointer[0]) - 1]
        )
        merge_pointer = merge_pointer[1:]
    return (context_pointer + merge_pointer.lstrip("0")).lstrip("/")
