#!/usr/bin/env python3
from collections import OrderedDict
from copy import deepcopy
import json
import os
from typing import Any, Dict, Iterable, List, Set, Tuple, Union
import jinja2
import jsonschema
from cidc_schemas.json_validation import _load_dont_validate_schema
from cidc_schemas.constants import SCHEMA_DIR

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(DOCS_DIR, "..")
TEMPLATES_DIR = os.path.join(DOCS_DIR, "templates")
HTML_DIR = os.path.join(DOCS_DIR, "docs")


# ----- Utility Functions ----- #
PATH_PARTS_TO_REMOVE: List[str] = [
    "adaptive",
    "analysis",
    "assay",
    "bam",
    "fastq",
    "template",
]
SCHEMA_STORE: Dict[Tuple[str, bool], dict] = dict()


def _flatten_allOf(schema: dict) -> dict:
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


def _load_schema(root: str, path: str, as_html: bool = True) -> dict:
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
        ret = _flatten_allOf(_load_dont_validate_schema(schema_path, SCHEMA_DIR))
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
    ret = _flatten_allOf(
        _load_dont_validate_schema(schema_path, SCHEMA_DIR, on_refs=_json_to_html)
    )
    SCHEMA_STORE[(schema_path, as_html)] = ret
    return ret


# load the protocol_identifier schema for easy use
PROTOCOL_IDENTIFIER_SCHEMA = _load_schema(
    SCHEMA_DIR, "clinical_trial.json", as_html=False
)["properties"]["protocol_identifier"]


def _nested_set(dic: dict, keys: Iterable[str], value: Any) -> None:
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


class Schema:

    name: str
    schema: dict
    required: Set[str]

    def __init__(self, name: str, schema: dict) -> None:
        """
        Sets self.schema and self.required
        Expands top-level and array-property allOf's

        Parameters
        ----------
        name: str
            the name of the schema
        schema: dict
            a jsonschemas definition
        """
        # flatten any top level allOf's
        _flatten_allOf(schema)

        # flatten array property allOf's
        for prop, definition in schema["properties"].items():
            if definition.get("type") == "array":
                _flatten_allOf(schema["properties"][prop]["items"])

        # set self.name, self.schema, and self.required
        self.name = name
        self.schema = schema
        self.required = self.schema.get("required", [])

    # ----- Utility Functions ----- #
    @staticmethod
    def _get_translated_merge_pointers(context: str, definition: dict) -> Set[str]:
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
            translated_merge_pointers.add(
                Schema._translate_merge_pointer(context, definition)
            )
        if "process_as" in definition:
            for process in definition["process_as"]:
                translated_merge_pointers.add(
                    Schema._translate_merge_pointer(context, process)
                )

        return translated_merge_pointers

    @staticmethod
    def _translate_merge_pointer(context_pointer: str, definition: dict) -> str:
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

    def _get_worksheet_values(
        self, root_object_pointer: str, sheet: dict
    ) -> Tuple[Set[str], Set[str]]:
        """
        Returns the sets of merge_pointers for metadata and data given in the worksheet

        Parameters
        ----------
        sheet: dict
            a jsonschemas definitions for a single worksheet of a template
            can have preamble_rows and/or data_columns

        Returns
        -------
        metadata_merge_pointers: Set[str]
            all translated absolute merge_pointers from the preamble_rows
        data_merge_pointers: Set[str]
            all translated absolute merge_pointers from the data_columns
        """
        metadata_merge_pointers = set()
        data_merge_pointers = set()

        if "preamble_rows" in sheet:
            # get the preamble ie metadata rows
            preamble_context: str = (
                "/".join(
                    [
                        root_object_pointer,
                        sheet.get("prism_preamble_object_pointer", ""),
                    ]
                )
                .replace("//", "/")
                .lstrip("/")
            )
            for row in sheet["preamble_rows"].values():
                metadata_merge_pointers.update(
                    Schema._get_translated_merge_pointers(preamble_context, row)
                )

        # get the data columns
        if "data_columns" in sheet:
            # start with the bases from the object pointers
            data_context: str = (
                "/".join(
                    [
                        root_object_pointer,
                        sheet.get("prism_preamble_object_pointer", ""),
                        sheet.get("prism_data_object_pointer", ""),
                    ]
                )
                .replace("//", "/")
                .lstrip("/")
            )
            for col_group in sheet["data_columns"].values():
                for definition in col_group.values():
                    data_merge_pointers.update(
                        Schema._get_translated_merge_pointers(data_context, definition)
                    )

        return metadata_merge_pointers, data_merge_pointers

    def _get_values(self, template_list: Iterable[dict]) -> Tuple[Set[str], Set[str]]:
        """
        Returns the metadata and data keys given across all templates and worksheets

        Parameters
        ----------
        template_list: Iterable[dict]
            a set of template definitions

        Returns
        -------
        metadata_merge_pointers: Set[str]
            all translated absolute merge_pointers from the preamble_rows
        data_merge_pointers: Set[str]
            all translated absolute merge_pointers from the data_columns
        """
        metadata_merge_pointers = set()
        data_merge_pointers = set()
        for template in template_list:
            for sheet in template["properties"]["worksheets"].values():
                sheet_md, sheet_data = self._get_worksheet_values(
                    root_object_pointer=template.get(
                        "prism_template_root_object_pointer", ""
                    ),
                    sheet=sheet,
                )
                metadata_merge_pointers.update(sheet_md)
                data_merge_pointers.update(sheet_data)

        return metadata_merge_pointers, data_merge_pointers

    @staticmethod
    def _handle_url(definition: dict) -> dict:
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
                definition["url"]
                .replace(".", "/")
                .replace("/html", ".json")
                .split("#")[0]
            )
            merge_pointer = (
                definition["url"].split("#")[-1] if definition["url"].count("#") else ""
            )
            schema = _load_schema(SCHEMA_DIR, schema_path)

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
                    k: Schema._handle_url(v) if isinstance(v, dict) else v
                    for k, v in definition["properties"].items()
                }

            if description:
                definition["description"] = description

        # if not elif as url can be an array itself
        if definition.get("type") == "array":
            return Schema._handle_array_url(definition)
        else:
            return definition

    @staticmethod
    def _handle_array_url(definition: dict) -> dict:
        """
        Handles schemas where type=array to translate items url and add a default description
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
        if "description" not in definition:
            definition["description"] = definition["items"].get("description", "")
        definition["items"] = Schema._handle_url(definition["items"])
        return definition


class AssaySchema(Schema):
    """
    Generates a structure for the jinja templates to turn into assay documentation.
    Also keeps the templates associated so they can be documented too.
    """

    name: str
    assay_templates: Dict[str, dict]
    analysis_templates: Dict[str, dict]
    schema: dict
    root: dict
    required: List[str]

    assay_metadata: Dict[str, dict]
    assay_data: Dict[str, dict]
    analysis_metadata: Dict[str, dict]
    analysis_data: Dict[str, dict]
    required_assay_metadata: List[str]
    required_assay_data: List[str]
    required_analysis_metadata: List[str]
    required_analysis_data: List[str]

    def __init__(
        self,
        name: str,
        schema: dict,
        assay_templates: Dict[str, dict],
        analysis_templates: Dict[str, dict],
    ) -> None:
        """
        Parameters
        ----------
        name: str
            the name of the schema
        schema: dict
            the jsonschemas definition for this assay from SCHEMA_DIR/assays
        assay_templates: Dict[str, dict]
            a mapping of the assay template(s) for this assay to their definition(s)
        analysis_templates: Dict[str, dict]
            a mapping of the analysis template(s) for this assay to their definition(s)
        """
        super().__init__(name=name, schema=schema)

        self.assay_templates = assay_templates
        self.analysis_templates = analysis_templates

        print("Processing", self.name)
        # set self.[required_]assay_[meta]data
        self.process_assays()
        # set self.[required_]analysis_[meta]data
        self.process_analyses()

    # ----- Utility Functions ----- #
    @staticmethod
    def _descend_dict(root: dict, levels: List[str]) -> dict:
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
            key "required" is added as a boolean, whether levels[-1] in final "required"
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
        required: bool = False
        for level in levels:
            # keep going while we can
            # if this is the last level, check if it's required
            if level == levels[-1]:
                required: bool = level in root.get("required", [])

            root = root[level]
            # descend into any items, properties, or non-artifact urls
            # single carve out for cytof source_fcs
            while not _all_the_way_down(root) and level != "source_fcs":
                if "items" in root:
                    root = root["items"]
                if "properties" in root and root["properties"]:
                    root = root["properties"]
                # updates in place
                Schema._handle_url(root)
                if "items" in root:
                    root = root["items"]
                if "properties" in root:
                    root = root["properties"]

        root["required"] = required
        return root

    def _process_merge_pointer(self, merge_pointer: str, data_store: dict) -> None:
        """
        Updates data by nested-setting the endpoint of the pointer with the part of the schema it points to
        The definition's "required" is a boolean based on the last step

        Parameters
        ----------
        merge_pointer: str
            the merge_pointer to fish out of self.root with _descend_dict()
        data_store: dict
            the nested dict to put the referenced definition
            set via _nested_set() which adds in place
        """
        root: dict = deepcopy(self.root)

        # break up the merge pointer into a set of keys
        # remove any array parts -- we'll always keep descending
        levels = [
            part
            for part in merge_pointer.split("/")
            if not part.isdigit() and part not in ("-", "")
        ]
        # skip down assays/self.assay_schema.name
        if levels[0] in ("assays", "analysis"):
            levels = levels[2:]
        else:
            # skip down clinical_data/
            levels = levels[1:]

        root = self._descend_dict(root, levels)

        # if merge_pointer points to a new item in the list
        # make sure we're all the way down and have a description
        if merge_pointer.endswith("-"):
            # updates in place
            Schema._handle_url(root)

            if "properties" in root:
                root = root["properties"]
            if root.get("type", "") == "array" and "description" not in root:
                root["description"] = root["items"].get("description", "")

        # update in place instead of returning
        _nested_set(data_store, levels, root)

    def _process_merge_pointers(self, merge_pointers: Set[str]) -> Dict[str, dict]:
        """
        Given the set of translated merge_pointers, return the definitions for the fields they point to in self.root
        The definitions are set in place ie nested, with bottom "required" as a boolean

        Parameters
        ----------
        merge_pointers: Set[str]
            the set of merge_pointers to fish out of self.root with _process_merge_pointer()

        Returns
        -------
        data: dict
            the nested dict of the referenced definitions
            descending following each merge_pointer yields the definition for that property
        """
        # if none given, just bail
        if not len(merge_pointers):
            return {}

        data = {}
        # sort them by the value that will be displayed
        for ptr in sorted(merge_pointers, key=lambda x: x.split("/")[-1]):
            if ptr.endswith("protocol_identifier"):
                data[ptr] = PROTOCOL_IDENTIFIER_SCHEMA
            else:
                # updates data in place
                self._process_merge_pointer(merge_pointer=ptr, data_store=data)

        return data

    # ----- Business Functions ----- #
    def process_assays(self) -> None:
        """
        Loads and sets:
            self.assay_metadata: Dict[str, dict]
            self.assay_data: Dict[str, dict]
            self.required_assay_metadata: List[str]
            self.required_assay_data: List[str]
        """
        # load the related schema
        if self.name == "rna":
            # if it's RNA, get v0
            version_schema = load_schemas(
                schema_dir=os.path.join(SCHEMA_DIR, "assays"),
                recursive=False,
            )[""]["rna_assay-v0"]
            self.root = version_schema["properties"]
            self.required.extend(version_schema["required"])
        else:
            self.root = self.schema["properties"]

        # get all merge_pointers referenced in the assay template(s)
        # split by metadata ie preamble vs data
        assay_metadata_merge_pointers, assay_data_merge_pointers = self._get_values(
            template_list=self.assay_templates.values()
        )
        self.assay_metadata: Dict[str, dict] = self._process_merge_pointers(
            merge_pointers=assay_metadata_merge_pointers
        )
        self.assay_data: Dict[str, dict] = self._process_merge_pointers(
            merge_pointers=assay_data_merge_pointers
        )

        self.required_assay_metadata: List[str] = [
            r for r in self.required if r in assay_metadata_merge_pointers
        ]
        self.required_assay_data: List[str] = [
            prop
            for prop, definition in self.assay_data.items()
            if definition.get("required")
        ]

    def process_analyses(self) -> None:
        """
        Loads and sets:
            self.analysis_metadata: Dict[str, dict]
            self.analysis_data: Dict[str, dict]
            self.required_analysis_metadata: List[str]
            self.required_analysis_data: List[str]
        """
        if self.name in ("atacseq", "ctdna", "microbiome", "rna", "tcr", "wes"):
            if self.name in ("atacseq", "rna"):
                version_schema = load_schemas(
                    schema_dir=os.path.join(
                        SCHEMA_DIR,
                        "assays",
                        "components",
                        "ngs",
                        self.name,
                    ),
                    recursive=False,
                )[""][f"{self.name}_analysis"]

            else:  # if self.name in ("ctdna", "microbiome", "tcr", "wes"):
                version_schema = load_schemas(
                    schema_dir=os.path.join(SCHEMA_DIR, "assays"),
                    recursive=False,
                )[""][f"{self.name}_analysis"]

                if self.name == "wes":
                    # also need to include tumor_only
                    version2 = load_schemas(
                        schema_dir=os.path.join(SCHEMA_DIR, "assays"),
                        recursive=False,
                    )[""][f"{self.name}_tumor_only_analysis"]
                    version_schema["properties"].update(version2["properties"])

            self.root = version_schema["properties"]

            self.required.extend(version_schema.get("required", []))
        else:
            self.root = self.schema["properties"]

        (
            analysis_metadata_merge_pointers,
            analysis_data_merge_pointers,
        ) = self._get_values(self.analysis_templates.values())

        self.analysis_metadata: Dict[str, dict] = self._process_merge_pointers(
            merge_pointers=analysis_metadata_merge_pointers
        )
        self.analysis_data: Dict[str, dict] = self._process_merge_pointers(
            merge_pointers=analysis_data_merge_pointers
        )

        self.required_analysis_metadata: List[str] = [
            r for r in self.required if r in analysis_metadata_merge_pointers
        ]
        self.required_analysis_data: List[str] = [
            prop
            for prop, definition in self.analysis_data.items()
            if definition.get("required")
        ]


class TemplateSchema(Schema):
    """
    Generates a structure for the jinja templates to turn into template documentation.
    Specifically handles process_as files and descriptions.
    """

    name: str
    schema: dict
    assay_schema: AssaySchema
    root: dict
    required: List[str]
    file_list: List[dict]

    def __init__(self, name: str, schema: dict, assay_schema: AssaySchema) -> None:
        """
        Parameters
        ----------
        name: str
            the name of the schema
        schema: dict
            a jsonschemas definition
        assay_schema: AssaySchema
            the prepared schema that defines the associated assay
        """
        super().__init__(name=name, schema=schema)
        self.assay_schema = assay_schema

        print("Processing", self.name)
        # go through each worksheet
        for worksheet_schema in self.schema["properties"]["worksheets"].values():
            if len(worksheet_schema.get("preamble_rows", {})):
                self._process_preamble(worksheet_schema=worksheet_schema)
            if len(worksheet_schema.get("data_columns", {})):
                self._process_data(worksheet_schema=worksheet_schema)

    def _update_from_merge_pointer(
        self,
        context_pointer: str,
        definition: dict,
    ) -> dict:
        """
        Updates a given property_schema from self.assay_schema using its merge_pointer
        Assert the existence of "merge_pointer" in property_schema

        Parameters
        ----------
        context_pointer: str
            absolute pointer to the location of `definition`
            from which merge_pointers are considered relative
        definition: dict
            a jsonschemas definition that must contain "merge_pointer"

        Returns
        -------
        definition: dict
            input after update
        """
        # grab the merge_pointer and chop it up
        merge_pointer = Schema._translate_merge_pointer(context_pointer, definition)
        levels = merge_pointer.split("/")

        # fill in array references to keep going down
        levels = [l for l in levels if l and l != "-" and not l.isdigit()]
        # skip down /assays/self.assay_schema.name if we have an AssaySchema
        if levels[0] in ("assays", "analysis") and isinstance(
            self.assay_schema, AssaySchema
        ):
            levels = levels[2:]
        elif levels[0] in ("clinical_data",):
            # skip down clinical_data/
            levels = levels[1:]
        else:
            # don't skip anything
            pass

        # get the base contexts from assay and/or analysis metadata/data
        if isinstance(self.assay_schema, AssaySchema):
            possible_contexts: Dict[str, dict] = {
                "assay_metadata": self.assay_schema.assay_metadata,
                "assay_data": self.assay_schema.assay_data,
                "analysis_metadata": self.assay_schema.analysis_metadata,
                "analysis_data": self.assay_schema.analysis_data,
            }
        else:  # isinstance(self.assay_schema, dict)
            possible_contexts: Dict[str, dict] = {
                "clinical_trial": self.assay_schema,
            }

        # descend into both contexts to find our leaf
        # keep going as long as at least one has the next leaf
        while len(levels) and any(
            levels[0] in context for context in possible_contexts.values()
        ):
            next_level: str = levels.pop(0)

            # while ugly, you can't iterate like this any other way
            for name in possible_contexts.keys():
                if possible_contexts[name] and next_level in possible_contexts[name]:
                    possible_contexts[name] = possible_contexts[name][next_level]
                    if "items" in possible_contexts[name]:
                        possible_contexts[name] = possible_contexts[name]["items"]
                    if (
                        "properties" in possible_contexts[name]
                        and possible_contexts[name]["properties"]
                    ):
                        possible_contexts[name] = possible_contexts[name]["properties"]
                    possible_contexts[name] = Schema._handle_url(
                        possible_contexts[name]
                    )
                    if "items" in possible_contexts[name]:
                        possible_contexts[name] = possible_contexts[name]["items"]
                    if "properties" in possible_contexts[name]:
                        possible_contexts[name] = possible_contexts[name]["properties"]
                else:
                    possible_contexts[name] = dict()

        # if we can't match at the way down, that's an issue
        if len(levels):
            assay_name: str = (
                self.assay_schema.name
                if isinstance(self.assay_schema, AssaySchema)
                else "clinical_trial"
            )
            print(list(possible_contexts["clinical_trial"].keys()))
            raise Exception(
                f"Cannot find {levels} in {assay_name}'s AssaySchema after descending for {merge_pointer}."
            )

        # update the schema and return it
        [definition.update(context) for context in possible_contexts.values()]
        return definition

    def _process_preamble(self, worksheet_schema: dict) -> None:
        """
        Update the given worksheet_schema with information from assay_schema
        Lines up by merge_pointer
        Asserts the existence of preamble_rows
        """
        # start with the bases from the object pointers
        context_pointer: str = (
            "/".join(
                [
                    self.schema.get("prism_template_root_object_pointer", ""),
                    worksheet_schema.get("prism_preamble_object_pointer", ""),
                ]
            )
            .replace("//", "/")
            .lstrip("/")
        )

        for prop_schema in worksheet_schema["preamble_rows"].values():
            # if it's protocol_identifier, just add that and keep going
            if prop_schema.get("merge_pointer", "").endswith("protocol_identifier"):
                prop_schema.update(PROTOCOL_IDENTIFIER_SCHEMA)
                continue

            # if we can, try to add the data from self.assay_schema
            if "merge_pointer" in prop_schema:
                self._update_from_merge_pointer(context_pointer, prop_schema)

    def _process_data(self, worksheet_schema: dict) -> None:
        """
        Update the given worksheet_schema with information from assay_schema
        Lines up by merge_pointer, and handles process_as
        Asserts the existence of data_columns
        """
        # start with the bases from the object pointers
        context_pointer: str = (
            "/".join(
                [
                    self.schema.get("prism_template_root_object_pointer", ""),
                    worksheet_schema.get("prism_preamble_object_pointer", ""),
                    worksheet_schema.get("prism_data_object_pointer", ""),
                ]
            )
            .replace("//", "/")
            .lstrip("/")
        )

        for table_schema in worksheet_schema["data_columns"].values():
            for prop_schema in table_schema.values():
                # if we can, try to add the data from self.assay_schema
                if "merge_pointer" in prop_schema:
                    self._update_from_merge_pointer(context_pointer, prop_schema)

                # handle process_as, asserting all entries have merge_pointer
                if "process_as" in prop_schema:
                    [
                        self._update_from_merge_pointer(context_pointer, entry)
                        for entry in prop_schema["process_as"]
                    ]
                    # for those with a parse_through artifacts, generate a relative_file_path
                    [
                        entry.update(
                            {"relative_file_path": entry["parse_through"].split("'")[1]}
                        )
                        for entry in prop_schema["process_as"]
                        if entry.get("is_artifact") and "parse_through" in entry
                    ]


# ----- Utility Functions ----- #
def _make_file(
    template: jinja2.Template,
    out_directory: str,
    scope: str,
    name: str,
    schema: Union[dict, AssaySchema, TemplateSchema],
):
    """
    template: jinja2.Template
        the jinja template to execute
    out_directory: str
        the directory in which to make the file
    scope: str
        passed to the template
        "" or "artifacts" expected for "entity.j2"
        "assays" for "assay.j2"
        "manifests" for "manifest.j2
    name: str
        passed to the template
        the name of the folder to make
    schema: Union[dict, AssaySchema, TemplateSchema]
        passed to the template
        dict expected for "entity.j2"
        AssaySchema expected for "assay.j2"
        TemplateSchema expected for "manifest.j2"
    """
    full_name = f"{scope}.{name}"
    if full_name.startswith("."):
        full_name = full_name[1:]

    # TODO remove try/catch
    try:
        # render the HTML to string
        entity_html = template.render(
            name=name,
            full_name=full_name,
            schema=schema,
            scope=scope,
            full_json_str="",
        )
    except Exception as e:
        if isinstance(schema, Schema):
            json.dump(schema.schema, open("problem_schema.json", "w"))
        else:
            json.dump(schema, open("problem_schema.json", "w"))

        raise Exception(f"Error rendering template documentation for {name}") from e

    else:
        # write this out
        with open(os.path.join(out_directory, f"{full_name}.html"), "w") as f:
            f.write(entity_html)


def load_schemas(
    schema_dir: str = SCHEMA_DIR,
    recursive: bool = True,
) -> Dict[str, Dict[str, dict]]:
    """
    Load all JSON schemas into a dictionary keyed on the
    schema directory. Values are dictionaries mapping entity
    names to loaded and validated entity schemas.
    If recursive, goes through all subdirectories as well
    """
    schemas = {}
    for root, _, paths in os.walk(schema_dir):
        root_schemas = {}
        for path in paths:
            if not path.endswith(".json"):
                continue

            schema_name = path[:-5].replace("/", ".")
            root_schemas[schema_name] = _load_schema(root, path)

        if len(root_schemas):
            relative_root = root.replace(schema_dir, "").replace("/", ".")
            relative_root = relative_root.replace(".", "", 1)
            schemas[relative_root] = root_schemas

        if not recursive:
            break

    return schemas


# ----- Schemas Loaders ----- #
def load_files_schemas() -> Dict[str, dict]:
    """
    Loads all artifact JSON schemas into a dict mapping entity names to the validated schema.
    """
    ret = load_schemas(schema_dir=os.path.join(SCHEMA_DIR, "artifacts"))[""]
    return {k.replace("artifact_", ""): v for k, v in ret.items()}


def load_assay_schemas() -> Dict[str, AssaySchema]:
    """
    Load all assay template JSON schemas into a dictionary
    and values are AssaySchema with the related template schemas and assay description.
    """
    # load assay and analysis template schemas
    all_assay_template_schemas: Dict[str, dict] = load_schemas(
        schema_dir=os.path.join(SCHEMA_DIR, "templates", "assays"),
    )[""]
    all_analysis_template_schemas: Dict[str, dict] = load_schemas(
        schema_dir=os.path.join(SCHEMA_DIR, "templates", "analyses"),
    )[""]

    # load assay DM schemas from SCHEMA_DIR/assays
    all_assay_schemas = load_schemas(
        schema_dir=os.path.join(SCHEMA_DIR, "assays"),
        recursive=False,
    )[""]

    # get generic assay categories
    assay_names = set(
        "_".join([t for t in template_name.split("_") if t not in PATH_PARTS_TO_REMOVE])
        for template_name in all_assay_template_schemas.keys()
    )
    # while no explicit assay templates, these do exist
    assay_names.update({"micsss", "wes_tumor_only"})

    # split templates by generic assay
    assay_template_schemas: Dict[str, Dict[str, dict]] = {
        assay_name: {
            template_name: template_schema
            for template_name, template_schema in all_assay_template_schemas.items()
            if "_".join(
                [t for t in template_name.split("_") if t not in PATH_PARTS_TO_REMOVE]
            )
            == assay_name
        }
        for assay_name in assay_names
    }
    analysis_template_schemas: Dict[str, Dict[str, dict]] = {
        assay_name: {
            template_name: template_schema
            for template_name, template_schema in all_analysis_template_schemas.items()
            if "_".join(
                [t for t in template_name.split("_") if t not in PATH_PARTS_TO_REMOVE]
            )
            == assay_name
        }
        for assay_name in assay_names
    }

    # map each assay to its corresponding schema
    assay_schemas = {
        "_".join([t for t in name.split("_") if t not in PATH_PARTS_TO_REMOVE]): schema
        for name, schema in all_assay_schemas.items()
    }
    # clinical is a top level
    assay_schemas["clinical_data"] = load_schemas(recursive=False)[""]["clinical_data"]

    # set up doc configs for each assay
    template_schemas_by_assay = {
        assay_name: AssaySchema(
            name=assay_name,
            schema=assay_schemas[assay_name],
            assay_templates=assay_template_schemas[assay_name],
            analysis_templates=analysis_template_schemas[assay_name],
        )
        for assay_name in sorted(assay_names)
    }

    return template_schemas_by_assay


def load_manifest_schemas() -> Dict[str, TemplateSchema]:
    """
    Load all manifest template JSON schemas into a dictionary
    Maps template names to their validated schema.
    """
    ret = load_schemas(schema_dir=os.path.join(SCHEMA_DIR, "templates", "manifests"))[
        ""
    ]
    clinical_trial_schema = _load_dont_validate_schema("clinical_trial.json")[
        "properties"
    ]
    return {
        # as keys are in relation to schema_dir, add a key before returning
        k: TemplateSchema(name=k, schema=v, assay_schema=clinical_trial_schema)
        for k, v in ret.items()
    }


def _load_available_assays_and_analyses() -> Dict[str, Dict[str, dict]]:
    ret = dict()

    components_dir: str = os.path.join(SCHEMA_DIR, "assays", "components")
    ret["available_assays"] = _load_schema(components_dir, "available_assays.json")
    ret["available_analyses"] = _load_schema(
        components_dir, "available_ngs_analyses.json"
    )

    def _update_url(dic: dict):
        if "components.ngs." in dic["url"]:
            print(dic["url"])
            # assays.components.ngs.{assay}.{assay}.html -> assays.{assay}.html
            dic["url"] = (
                ".".join(dic["url"].replace("components.ngs.", "").split(".")[:-2])
                + ".html"
            )
            print(dic["url"])

        if "_" in dic["url"] and "misc_data" not in dic["url"]:
            dic["url"] = "_".join(dic["url"].split("_")[:-1]) + ".html"

    # update urls to point to the correct place
    for schema in ret.values():
        for prop_dict in schema["properties"].values():
            pass
            if "url" in prop_dict:
                _update_url(prop_dict)
            elif "items" in prop_dict and "url" in prop_dict["items"]:
                _update_url(prop_dict["items"])

    return ret


def load_toplevel_schemas(
    keys: List[str] = [
        "aliquot",
        "clinical_trial",
        "collection_event",
        "participant",
        "sample",
        "shipping_core",
    ],
) -> Dict[str, Dict[str, dict]]:
    """
    Load just the schemas in SCHEMA_DIR into a dict mapping entity names to the validated schema.
    """
    # only get the first level of schemas, with key == ""
    toplevel_schemas: Dict[str, dict] = load_schemas(
        schema_dir=SCHEMA_DIR, recursive=False
    )

    # only keep the ones we"ve specified
    ret = {k: v for k, v in toplevel_schemas[""].items() if k in keys}

    # add these because we need them to link
    if "clinical_trial" in keys:
        ret.update(_load_available_assays_and_analyses())

    return ret


# ----- Key Business Function ----- #
def generate_docs(out_directory: str = HTML_DIR):
    """
    Generate documentation based on the schemas found in `SCHEMA_DIR`.
    """

    # Empty contents of docs/docs directory to prevent old html renders from showing up
    for filename in os.listdir(out_directory):
        os.unlink(out_directory + "/" + filename)

    templateLoader = jinja2.FileSystemLoader(TEMPLATES_DIR)
    templateEnv = jinja2.Environment(loader=templateLoader)

    # Generate index template
    schemas_groups = OrderedDict()
    schemas_groups[""]: Dict[str, dict] = load_toplevel_schemas()
    schemas_groups["assays"]: Dict[str, AssaySchema] = load_assay_schemas()
    schemas_groups["manifests"]: Dict[str, TemplateSchema] = load_manifest_schemas()
    schemas_groups["files"]: Dict[
        str,
    ] = load_files_schemas()

    index_template = templateEnv.get_template("index.j2")
    index_html = index_template.render(schema_groups=schemas_groups)
    with open(os.path.join(out_directory, "index.html"), "w") as f:
        f.write(index_html)

    # Load all of the different template types to choose from later
    assay_template = templateEnv.get_template("assay.j2")
    entity_template = templateEnv.get_template("entity.j2")
    template_template = templateEnv.get_template("template.j2")

    scope: str
    entities_dict: Dict[str, Union[dict, AssaySchema, TemplateSchema]]
    for scope, entities_dict in schemas_groups.items():
        # Determine whether these are assays, templates, or normal entities
        if scope == "assays":
            template = assay_template
        elif scope == "manifests":
            template = template_template
        else:  # scope in ("", "files")
            template = entity_template

        # Generate the html files
        name: str
        schema: Union[dict, AssaySchema, TemplateSchema]
        for name, schema in entities_dict.items():
            _make_file(template, out_directory, scope, name, schema)

    # Generate templates for each assay as well
    for assay_name, assay_schema in schemas_groups["assays"].items():
        scope = f"assays.{assay_name}"

        for upload_name, upload_schema in list(
            assay_schema.assay_templates.items()
        ) + list(assay_schema.analysis_templates.items()):
            _make_file(
                template_template,
                out_directory,
                scope,
                upload_name,
                TemplateSchema(
                    name=upload_name,
                    schema=upload_schema,
                    assay_schema=assay_schema,
                ),
            )


if __name__ == "__main__":
    generate_docs()
