#!/usr/bin/env python3
from collections import OrderedDict
from copy import deepcopy
import jinja2
import json
import os
from typing import Dict, Iterable, List, Set, Tuple, Union

from cidc_schemas.json_validation import _load_dont_validate_schema
from cidc_schemas.constants import SCHEMA_DIR
import utils

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(DOCS_DIR, "templates")
OLD_UPLOAD_DIR = os.path.join(DOCS_DIR, "old_uploads")
HTML_DIR = os.path.join(DOCS_DIR, "docs")

# load the protocol_identifier schema for easy use
PROTOCOL_IDENTIFIER_SCHEMA = utils.load_schema(
    SCHEMA_DIR, "clinical_trial.json", as_html=False
)["properties"]["protocol_identifier"]


def _get_worksheet_merge_pointers(
    root_object_pointer: str, sheet: dict
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
                utils.get_translated_merge_pointers(preamble_context, row)
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
                    utils.get_translated_merge_pointers(data_context, definition)
                )

    return metadata_merge_pointers, data_merge_pointers


def _get_all_merge_pointers(template_list: Iterable[dict]) -> Dict[str, Set[str]]:
    """
    Returns the metadata and data keys given across all templates and worksheets

    Parameters
    ----------
    template_list: Iterable[dict]
        a set of template definitions

    Returns
    -------
    Dict[str, Set[str]]
        with the following keys
        "metadata": Set[str]
            all translated absolute merge_pointers from the preamble_rows
        "data": Set[str]
            all translated absolute merge_pointers from the data_columns
    """
    metadata_merge_pointers = set()
    data_merge_pointers = set()
    for template in template_list:
        for sheet in template["properties"]["worksheets"].values():
            sheet_md, sheet_data = _get_worksheet_merge_pointers(
                root_object_pointer=template.get(
                    "prism_template_root_object_pointer", ""
                ),
                sheet=sheet,
            )
            metadata_merge_pointers.update(sheet_md)
            data_merge_pointers.update(sheet_data)

    return {"metadata": metadata_merge_pointers, "data": data_merge_pointers}


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
        utils.flatten_allOf(schema)

        # flatten array property allOf's
        for prop, definition in schema["properties"].items():
            if definition.get("type") == "array":
                utils.flatten_allOf(schema["properties"][prop]["items"])

        # set self.name, self.schema, and self.required
        self.name = name
        self.schema = schema
        # protcol_identifier always required
        self.required = set(self.schema.get("required", []) + ["protocol_identifier"])


class AssaySchema(Schema):
    """
    Generates a structure for the jinja templates to turn into assay documentation.
    Also keeps the templates associated so they can be documented too.
    """

    name: str
    schema: dict
    required: Set[str]
    templates: Dict[str, Dict[str, dict]]
    # optional keys "assay" and "analysis" are mapping of names to templates

    # will always have keys "assay" and "analysis"
    # each with keys "metadata" and "data"
    merge_pointers: Dict[str, Dict[str, Set[str]]]

    root: dict
    assay_metadata: Dict[str, dict]
    assay_data: Dict[str, dict]
    analysis_metadata: Dict[str, dict]
    analysis_data: Dict[str, dict]

    def __init__(
        self,
        name: str,
        schema: dict,
        templates: Dict[str, Dict[str, dict]] = dict(),
    ) -> None:
        """
        Parameters
        ----------
        name: str
            the name of the schema
        schema: dict
            the jsonschemas definition for this assay from SCHEMA_DIR/assays
        assay_templates: Dict[str, dict] = dict()
            a mapping of the assay template(s) for this assay to their definition(s)
        analysis_templates: Dict[str, dict] = dict()
            a mapping of the analysis template(s) for this assay to their definition(s)
        merge_pointers: Dict[str, Dict[str, Set[str]]] = dict()
            a dict with keys "assay" and "analysis"
            each themselves dicts with keys "metadata" and "data"
            which are themselves a list of merge_pointers within this assay
        """
        super().__init__(name=name, schema=schema)

        self.templates = templates

        self.merge_pointers: Dict[str, Dict[str, Set[str]]] = {
            "assay": _get_all_merge_pointers(
                template_list=self.templates.get("assay", {}).values()
            ),
            "analysis": _get_all_merge_pointers(
                self.templates.get("analysis", {}).values()
            ),
        }

        print("Processing", self.name)
        # set self.assay_[meta]data
        self.process_assay_merge_pointers()
        # set self.analysis_[meta]data
        self.process_analysis_merge_pointers()

    def _add_merge_pointer_to_data_store(
        self, merge_pointer: str, data_store: dict
    ) -> None:
        """
        Updates data by nested-setting the endpoint of the pointer with the part of the schema it points to
        The definition's "required" is a boolean based on the last step

        Parameters
        ----------
        merge_pointer: str
            the merge_pointer to fish out of self.root with utils.descend_dict()
        data_store: dict
            the nested dict to put the referenced definition
            set via utils.nested_set() which adds in place
        """
        root: dict = deepcopy(self.root)

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

        # skip down assays/self.assay_schema.name
        if levels[0] in ("assays", "analysis"):
            levels = levels[2:]
            array_pointers = [l[2:] for l in array_pointers]
        else:
            # skip down clinical_data/
            levels = levels[1:]
            array_pointers = [l[1:] for l in array_pointers]

        root, required = utils.descend_dict(root, levels)
        self.required.update(required)

        # if merge_pointer points to a new item in the list
        # make sure we're all the way down and have a description
        if merge_pointer.endswith("-"):
            # updates in place
            utils.load_subschema_from_url(root)
            self.required.update(root.get("required", []))

            if "properties" in root:
                root = root["properties"]
                self.required.update(root.get("required", []))
            if root.get("type", "") == "array" and "description" not in root:
                root["description"] = root["items"].get("description", "")

        # update in place instead of returning
        utils.nested_set(data_store, levels, root)

        # for every intermediate array found before add {"items": True}
        # so the template knows this is an array and not an object
        for pointer_to_array in array_pointers:
            # unneeded at the top level since docs are for a singular upload
            if len(pointer_to_array):
                utils.nested_set(data_store, pointer_to_array + ["items"], True)

    def _get_merge_pointer_definitions(
        self, merge_pointers: Set[str]
    ) -> Dict[str, dict]:
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
                self._add_merge_pointer_to_data_store(
                    merge_pointer=ptr, data_store=data
                )

        return data

    # ----- Business Functions ----- #
    def process_assay_merge_pointers(
        self,
    ) -> None:
        """
        Loads and sets:
            self.assay_metadata: Dict[str, dict]
            self.assay_data: Dict[str, dict]
        """
        # load the related schema
        if self.name == "rna":
            # if it's RNA, get v0
            version_schema = utils.load_schemas_in_directory(
                schema_dir=os.path.join(SCHEMA_DIR, "assays"),
                recursive=False,
            )[""]["rna_assay-v0"]
            self.root = version_schema["properties"]
            self.required.update(version_schema["required"])
        else:
            self.root = self.schema["properties"]
            self.required.update(self.root.get("required", []))

        self.assay_metadata: Dict[str, dict] = self._get_merge_pointer_definitions(
            merge_pointers=self.merge_pointers["assay"]["metadata"]
        )
        self.assay_data: Dict[str, dict] = self._get_merge_pointer_definitions(
            merge_pointers=self.merge_pointers["assay"]["data"]
        )

    def process_analysis_merge_pointers(
        self,
    ) -> None:
        """
        Loads and sets:
            self.analysis_metadata: Dict[str, dict]
            self.analysis_data: Dict[str, dict]
        """
        if self.name in ("atacseq", "ctdna", "microbiome", "rna", "tcr", "wes"):
            if self.name in ("atacseq", "rna"):
                version_schema = utils.load_schemas_in_directory(
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
                version_schema = utils.load_schemas_in_directory(
                    schema_dir=os.path.join(SCHEMA_DIR, "assays"),
                    recursive=False,
                )[""][f"{self.name}_analysis"]

                if self.name == "wes":
                    # also need to include tumor_only
                    version2 = utils.load_schemas_in_directory(
                        schema_dir=os.path.join(SCHEMA_DIR, "assays"),
                        recursive=False,
                    )[""][f"{self.name}_tumor_only_analysis"]
                    version_schema["properties"].update(version2["properties"])

            self.root = version_schema["properties"]

            self.required.update(version_schema.get("required", []))
        else:
            self.root = self.schema["properties"]
            self.required.update(self.root.get("required", []))

        self.analysis_metadata: Dict[str, dict] = self._get_merge_pointer_definitions(
            merge_pointers=self.merge_pointers["analysis"]["metadata"]
        )
        self.analysis_data: Dict[str, dict] = self._get_merge_pointer_definitions(
            merge_pointers=self.merge_pointers["analysis"]["data"]
        )


class TemplateSchema(Schema):
    """
    Generates a structure for the jinja templates to turn into template documentation.
    Specifically handles process_as files and descriptions.
    """

    name: str
    schema: dict
    assay_schema: AssaySchema
    root: dict
    required: Set[str]
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

    def _update_definition_from_merge_pointer(
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
        merge_pointer = utils.translate_merge_pointer(context_pointer, definition)
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
                    if "items" in possible_contexts[name] and not isinstance(
                        # added in _add_merge_pointer_to_data_store for template
                        possible_contexts[name]["items"],
                        bool,
                    ):
                        possible_contexts[name] = possible_contexts[name]["items"]
                    if (
                        "properties" in possible_contexts[name]
                        and possible_contexts[name]["properties"]
                    ):
                        possible_contexts[name] = possible_contexts[name]["properties"]
                    possible_contexts[name] = utils.load_subschema_from_url(
                        possible_contexts[name]
                    )
                    if "items" in possible_contexts[name] and not isinstance(
                        # added in _add_merge_pointer_to_data_store for template
                        possible_contexts[name]["items"],
                        bool,
                    ):
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

        for prop_name, prop_schema in worksheet_schema["preamble_rows"].items():
            # if it's protocol_identifier, just add that and keep going
            if prop_schema.get("merge_pointer", "").endswith("protocol_identifier"):
                prop_schema.update(PROTOCOL_IDENTIFIER_SCHEMA)
                self.required.add(prop_name)
                continue

            # if we can, try to add the data from self.assay_schema
            if "merge_pointer" in prop_schema:
                self._update_definition_from_merge_pointer(context_pointer, prop_schema)

            if not prop_schema.get("allow_empty", False):
                self.required.add(prop_name)

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
            for prop_name, prop_schema in table_schema.items():
                if not prop_schema.get("allow_empty", False):
                    self.required.add(prop_name)

                # if we can, try to add the data from self.assay_schema
                if "merge_pointer" in prop_schema:
                    self._update_definition_from_merge_pointer(
                        context_pointer, prop_schema
                    )

                # handle process_as, asserting all entries have merge_pointer
                if "process_as" in prop_schema:
                    [
                        self._update_definition_from_merge_pointer(
                            context_pointer, entry
                        )
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

    # render the HTML to string
    entity_html = template.render(
        name=name,
        full_name=full_name,
        schema=schema,
        scope=scope,
        full_json_str="",
    )

    # write this out
    with open(os.path.join(out_directory, f"{full_name}.html"), "w") as f:
        f.write(entity_html)


# ----- Schemas Loaders ----- #
def load_files_schemas() -> Dict[str, dict]:
    """
    Loads all artifact JSON schemas into a dict mapping entity names to the validated schema.
    """
    ret = utils.load_schemas_in_directory(
        schema_dir=os.path.join(SCHEMA_DIR, "artifacts")
    )[""]
    return {k.replace("artifact_", ""): v for k, v in ret.items()}


def load_assay_schemas() -> Dict[str, AssaySchema]:
    """
    Load all assay template JSON schemas into a dictionary
    and values are AssaySchema with the related template schemas and assay description.
    """
    # load assay and analysis template schemas
    all_assay_template_schemas: Dict[str, dict] = utils.load_schemas_in_directory(
        schema_dir=os.path.join(SCHEMA_DIR, "templates", "assays"),
    )[""]
    all_analysis_template_schemas: Dict[str, dict] = utils.load_schemas_in_directory(
        schema_dir=os.path.join(SCHEMA_DIR, "templates", "analyses"),
    )[""]
    all_analysis_template_schemas.update(
        utils.load_schemas_in_directory(
            schema_dir=os.path.join(SCHEMA_DIR, "templates", "analyses"),
        )[""]
    )

    # load assay DM schemas from SCHEMA_DIR/assays
    all_assay_schemas = utils.load_schemas_in_directory(
        schema_dir=os.path.join(SCHEMA_DIR, "assays"),
        recursive=False,
    )[""]

    parts_to_remove: List[str] = [
        "adaptive",
        "analysis",
        "assay",
        "bam",
        "fastq",
        "template",
    ]

    def strip(s: str) -> str:
        # don't cut wes analysis, handled separately from wes assay
        if "wes" in s and "analysis" in s:
            return s
        else:
            return "_".join([t for t in s.split("_") if t not in parts_to_remove])

    # get generic assay categories
    assay_names = set(
        strip(template_name) for template_name in all_assay_template_schemas.keys()
    )
    # while no explicit assay templates, these do exist
    # `wes[_tumor_only]_analysis` to put wes analysis in separate from assay
    assay_names.update({"micsss", "wes_tumor_only_analysis", "wes_analysis"})

    # split templates by generic assay
    assay_template_schemas: Dict[str, Dict[str, dict]] = {
        assay_name: {
            template_name: template_schema
            for template_name, template_schema in all_assay_template_schemas.items()
            if strip(template_name) == assay_name
        }
        for assay_name in assay_names
    }
    analysis_template_schemas: Dict[str, Dict[str, dict]] = {
        assay_name: {
            template_name: template_schema
            for template_name, template_schema in all_analysis_template_schemas.items()
            # handle wes analysis separately from wes assay
            if (
                ("wes" not in template_name or "analysis" not in template_name)
                and strip(template_name) == assay_name
            )
            or (
                "wes" in template_name
                and "analysis" in template_name
                and assay_name == template_name.replace("_template", "")
            )
        }
        for assay_name in assay_names
    }

    # map each assay to its corresponding schema
    assay_schemas = {strip(name): schema for name, schema in all_assay_schemas.items()}
    # clinical is a top level
    assay_schemas["clinical_data"] = utils.load_schemas_in_directory(recursive=False)[
        ""
    ]["clinical_data"]

    # set up doc configs for each assay
    template_schemas_by_assay = {
        assay_name: AssaySchema(
            name=assay_name,
            schema=assay_schemas[assay_name],
            templates={
                "assay": assay_template_schemas[assay_name],
                "analysis": analysis_template_schemas[assay_name],
            },
        )
        for assay_name in sorted(assay_names)
    }

    # add doc configs for old uploads
    for path in os.listdir(OLD_UPLOAD_DIR):
        if not path.endswith(".json"):
            continue

        # remove the unneeded parts; separately to not require both
        upload_name: str = path.replace("_template", "").replace(".json", "")
        # handle wes analysis separately from wes assay
        if "wes" not in upload_name or "analysis" not in upload_name:
            upload_name = upload_name.replace("_analysis", "")

        assay_name: str = upload_name.replace("_old", "")

        schema = json.load(open(os.path.join(OLD_UPLOAD_DIR, path)))

        template_schemas_by_assay[upload_name] = AssaySchema(
            name=assay_name,
            schema=template_schemas_by_assay[assay_name].schema,
            templates={"analysis": {upload_name: schema}},
        )

    return template_schemas_by_assay


def load_manifest_schemas() -> Dict[str, TemplateSchema]:
    """
    Load all manifest template JSON schemas into a dictionary
    Maps template names to their validated schema.
    """
    ret = utils.load_schemas_in_directory(
        schema_dir=os.path.join(SCHEMA_DIR, "templates", "manifests")
    )[""]
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
    ret["available_assays"] = utils.load_schema(components_dir, "available_assays.json")
    ret["available_analyses"] = utils.load_schema(
        components_dir, "available_ngs_analyses.json"
    )

    def _update_url(name: str, dic: dict):
        if "components.ngs." in dic["url"]:
            # assays.components.ngs.{assay}.{assay}.html -> assays.{assay}.html
            dic["url"] = (
                ".".join(dic["url"].replace("components.ngs.", "").split(".")[:-2])
                + ".html"
            )

        if (
            "_" in dic["url"]
            and "misc_data" not in dic["url"]
            and ("wes" not in dic["url"] or "analysis" not in dic["url"])
        ):
            dic["url"] = "_".join(dic["url"].split("_")[:-1]) + ".html"

        if "_old" in name:
            dic["url"] = dic["url"].replace(".html", "_old.html")

    # update urls to point to the correct place
    for schema in ret.values():
        for prop_name, prop_dict in schema["properties"].items():
            pass
            if "url" in prop_dict:
                _update_url(prop_name, prop_dict)
            elif "items" in prop_dict and "url" in prop_dict["items"]:
                _update_url(prop_name, prop_dict["items"])

    return ret


def load_toplevel_schemas(
    keys: List[str] = [
        "clinical_trial",
        "participant",
        "sample",
        "shipping_core",
    ],
) -> Dict[str, Dict[str, dict]]:
    """
    Load just the schemas in SCHEMA_DIR into a dict mapping entity names to the validated schema.
    """
    # only get the first level of schemas, with key == ""
    toplevel_schemas: Dict[str, dict] = utils.load_schemas_in_directory(
        schema_dir=SCHEMA_DIR, recursive=False
    )

    # only keep the ones we"ve specified
    ret = {k: v for k, v in toplevel_schemas[""].items() if k in keys}

    # add these because we need them to link from clinical_data
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
            assay_schema.templates.get("assay", {}).items()
        ) + list(assay_schema.templates.get("analysis", {}).items()):
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
