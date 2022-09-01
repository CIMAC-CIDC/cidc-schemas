#!/usr/bin/env python3
from collections import OrderedDict
import json
import os
from typing import Dict, Iterable, List, Set, Tuple
import jinja2
import jsonschema
from cidc_schemas.json_validation import _load_dont_validate_schema
from cidc_schemas.constants import SCHEMA_DIR

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(DOCS_DIR, "..")
TEMPLATES_DIR = os.path.join(DOCS_DIR, "templates")
HTML_DIR = os.path.join(DOCS_DIR, "docs")


class Schema:

    name: str
    schema: dict
    required: List[str]

    def __init__(self, name: str, schema: dict):
        self.name = name

        # set self.schema and self.required
        self.schema = schema
        self.required = self.schema.get("required", [])
        if not "properties" in self.schema:
            self.schema["properties"] = {}

        while "allOf" in self.schema:
            for other_schema in self.schema.pop("allOf", []):
                if "properties" in other_schema:
                    self.schema["properties"].update(other_schema["properties"])
                if "required" in other_schema:
                    self.required.extend(other_schema["required"])
                    self.required = list(set(self.required))

        for prop, definition in self.schema["properties"].items():
            if definition.get("type") == "array":
                while "allOf" in self.schema["properties"][prop]["items"]:
                    for other_schema in self.schema["properties"][prop]["items"].pop(
                        "allOf", []
                    ):
                        if "properties" in other_schema:
                            self.schema["properties"][prop]["items"][
                                "properties"
                            ].update(other_schema["properties"])
                        if "required" in other_schema:
                            self.schema["properties"][prop]["items"]["required"].extend(
                                other_schema["required"]
                            )
                            self.schema["properties"][prop]["items"]["required"] = list(
                                set(self.required)
                            )

    # ----- Utility Functions ----- #
    @staticmethod
    def _translate_merge_pointer(context: str, definition: dict):
        context = context.rstrip("-")
        if (
            definition["merge_pointer"][0].isdigit()
            and definition["merge_pointer"][0] != "0"
        ):
            context = "/".join(
                context.split("/")[: -int(definition["merge_pointer"][0])]
            )
        return context + definition["merge_pointer"].lstrip("0")

    @staticmethod
    def _get_values(template_list: Iterable[dict]) -> Tuple[Set[str], Set[str]]:
        """Returns the metadata and data keys given in the across all templates and worksheets"""
        metadata_values = set()
        data_values = set()
        for template in template_list:
            for sheet in template["properties"]["worksheets"].values():
                if "preamble_rows" in sheet:
                    for row in sheet["preamble_rows"].values():
                        if not row.get("do_not_merge", False):
                            metadata_values.add(row["merge_pointer"].split("/")[-1])
                if "data_columns" in sheet:
                    data_context = sheet["prism_data_object_pointer"]
                    for col_group in sheet["data_columns"].values():
                        for definition in col_group.values():
                            if "merge_pointer" in definition:
                                data_values.add(
                                    Schema._translate_merge_pointer(
                                        data_context, definition
                                    )
                                )
                            if "process_as" in definition:
                                for process in definition["process_as"]:
                                    data_values.add(
                                        Schema._translate_merge_pointer(
                                            data_context, process
                                        )
                                    )

        return metadata_values, data_values

    @staticmethod
    def _handle(v: dict) -> dict:
        """Handles urls in loading the subschema and default descriptions for type=array"""
        # don't translate artifact urls into a schema
        if "type" not in v and "url" in v and "artifacts" not in v["url"]:
            schema_path = (
                v["url"].replace(".", "/").replace("/html", ".json").split("#")[0]
            )
            merge_pointer = v["url"].split("#")[-1] if v["url"].count("#") else ""
            schema = _load_schema(SCHEMA_DIR, schema_path)

            # save the highest description to use
            description: str = v.get("description", "")
            # definitions first because properties can point here
            if merge_pointer in schema.get("definitions", {}):
                v.update(schema["definitions"][merge_pointer])
            elif merge_pointer in schema.get("properties", {}):
                v.update(schema["properties"][merge_pointer])
            else:
                v.update(schema)

            # include any lower ones too
            # eg ihc > antibody > antibody
            if "properties" in v:
                v.update(Schema._handle(v["properties"]))
                v.update({"_nested": True})

            if description:
                v["description"] = description

        # if not elif as url can be an array itself
        if v.get("type") == "array":
            return Schema._handle_array(v)

        return v

    @staticmethod
    def _handle_array(v: dict) -> dict:
        """Handles schemas where type=array to translate items url and add a default description"""
        if "description" not in v:
            v["description"] = v["items"].get("description", "")
        return Schema._handle(v["items"])

    @staticmethod
    def _handle_process_as(
        prop_name: str, prop_schema: dict, data_pointer: str, assay_schema: dict
    ) -> Tuple[str, dict]:
        if "merge_pointer" in prop_schema:
            merge_pointer = prop_schema["merge_pointer"].replace("/-", "")
        else:
            merge_pointer = ""
        levels = merge_pointer.split("/")
        if levels[0].isdigit() and int(levels[0]):
            levels = data_pointer.split("/")[: -int(levels[0])] + levels[1:]
        else:
            levels = data_pointer.split("/") + levels[:]
        levels = [l for l in levels if l and l != "-" and not l.isdigit()]

        return_name: str = levels[-1]

        # prop_required: bool = prop_name in required
        if (
            not prop_schema.get("type_ref")
            or prop_schema.get("do_not_merge", False)
            or len(levels) == 0
        ):
            return {return_name: prop_schema}
        else:
            context = {levels[0]: {}}
            if levels[0] in assay_schema.assay_data:
                context[levels[0]].update(assay_schema.assay_data[levels[0]].copy())
            if levels[0] in assay_schema.analysis_data:
                context[levels[0]].update(assay_schema.analysis_data[levels[0]].copy())

            if not len(context[levels[0]]):
                raise Exception(
                    f"Cannot find {levels[0]} in {assay_schema.name}'s AssaySchema for {prop_name}."
                )

            while len(levels) and levels[0] in context:
                next_level = levels.pop(0)
                context = context[next_level]

            if len(levels):
                raise Exception(
                    f"Cannot find {levels} in {assay_schema.name}'s AssaySchema after descending for {prop_name}."
                )

            if "parse_through" in prop_schema:
                context["relative_file_path"] = prop_schema["parse_through"].split("'")[
                    1
                ]
            else:
                context["relative_file_path"] = prop_name

            return {return_name: context}


class AssaySchema(Schema):
    """
    Generates a structure for the jinja templates to turn into assay documentation.
    Also keeps the templates associated so they can be documented too.
    """

    name: str
    assays: Dict[str, dict]
    analyses: Dict[str, dict]
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
        assays: Dict[str, dict],
        analyses: Dict[str, dict],
    ):
        super().__init__(name=name, schema=schema)

        self.assays = assays
        self.analyses = analyses

        # set self.[required_]assay_[meta]data
        self.process_assays()
        # set self.[required_]analysis_[meta]data
        self.process_analyses()

    # ----- Utility Functions ----- #
    def _process_data(self, data_values: Set[str]) -> Dict[str, dict]:
        """
        Given the set of translated merge_pointers, return the definitions for the fields they point to
        Group data as hierarchical properties
        """

        def nested_set(dic, keys, value):
            for key in keys[:-1]:
                dic = dic.setdefault(key, {"_nested": True})
            dic[keys[-1]] = value

        data = {}
        if len(data_values):
            for k in sorted(data_values):
                root = self.root.copy()
                levels = [
                    part
                    for part in k.split("/")
                    if not part.isdigit() and part not in ("-", "")
                ]
                for level in levels:
                    required: bool = False
                    if level in root:
                        if "required" in root:
                            if isinstance(root["required"], bool):
                                required: bool = root["required"]
                            elif isinstance(root["required"], Iterable):
                                required: bool = level in root["required"]
                        root = root[level]

                        while level not in root and (
                            "items" in root
                            or "properties" in root
                            or (
                                # see _process
                                "url" in root
                                and "type" not in root
                                and "artifacts" not in root["url"]
                            )
                        ):
                            if "items" in root:
                                root = root["items"]
                            elif "properties" in root:
                                root = root["properties"]
                            else:  # "url" in root:
                                # updates in place
                                self._handle(root)

                if k.endswith("-"):
                    # updates in place
                    self._handle(root)

                    # make sure we're all the way at the bottom
                    if "properties" in root:
                        root = root["properties"]
                    if root.get("type", "") == "array" and "description" not in root:
                        root["description"] = root["items"].get("description", "")

                root["required"] = required
                levels[0] = levels[0].replace(self.name, "").strip("_")

                nested_set(data, levels, root)

        return data

    @staticmethod
    def _handle_process_metadata(
        metadata_values: Set[str], items: Iterable[Tuple[str, dict]]
    ):
        def inner(context: Iterable[Tuple[str, dict]]) -> dict:
            return {
                k: Schema._handle(v.copy())
                for k, v in sorted(context, key=lambda x: x[0])
            }

        ret = inner(items)
        for k, v in items:
            if "url" in v:
                v = Schema._handle(v)
            if "properties" in v:
                ret[k] = inner(v["properties"].items())
                ret[k].update({"_nested": True})
        return ret

    def _process_metadata(self, metadata_values: Set[str]) -> Tuple[dict, List[str]]:
        """Given the set of translated merge_pointers, return the definitions for the fields they point to"""
        items = (
            list(self.schema.get("properties", {}).items())
            + list(self.schema.get("definitions", {}).items())
            + list(self.root.items())
        )
        return self._handle_process_metadata(metadata_values, items)

    # ----- Business Functions ----- #
    def process_assays(self) -> None:
        if self.name == "rna":
            version_schema = load_schemas(
                schema_dir=os.path.join(SCHEMA_DIR, "assays"),
                recursive=False,
                as_html=False,
            )[""]["rna_assay-v0"]
            self.root = version_schema["properties"]
            self.required.extend(version_schema["required"])
        elif self.name == "olink":
            self.root = self.schema["definitions"]["batch"]["properties"]
            self.required.extend(self.schema["definitions"]["batch"]["required"])
        else:
            self.root = self.schema["properties"]

        assay_metadata_values, assay_data_values = self._get_values(
            self.assays.values()
        )
        self.assay_metadata = self._process_metadata(assay_metadata_values)
        self.assay_data = self._process_data(assay_data_values)

        self.required_assay_metadata = [
            r for r in self.required if r in assay_metadata_values
        ]
        self.required_assay_data = [
            prop
            for prop, definition in self.assay_data.items()
            if definition.get("required")
        ]

    def process_analyses(self) -> None:
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
                    as_html=False,
                )[""][f"{self.name}_analysis"]

            else:  # if self.name in ("ctdna", "microbiome", "tcr", "wes"):
                version_schema = load_schemas(
                    schema_dir=os.path.join(SCHEMA_DIR, "assays"),
                    recursive=False,
                    as_html=False,
                )[""][f"{self.name}_analysis"]

                if self.name == "wes":
                    # also need to include tumor_only
                    version2 = load_schemas(
                        schema_dir=os.path.join(SCHEMA_DIR, "assays"),
                        recursive=False,
                        as_html=False,
                    )[""][f"{self.name}_tumor_only_analysis"]
                    version_schema["properties"].update(version2["properties"])
                else:  # if self.name in ("ctdna", "microbiome", "tcr")
                    version_schema = version_schema["definitions"]["batch"]

            self.root = version_schema["properties"]
            self.required.extend(version_schema.get("required", []))
        else:
            self.root = self.schema["properties"]

        analysis_metadata_values, analysis_data_values = self._get_values(
            self.analyses.values()
        )

        self.analysis_metadata = self._process_metadata(analysis_metadata_values)
        self.analysis_data = self._process_data(analysis_data_values)

        self.required_analysis_metadata = [
            r for r in self.required if r in analysis_metadata_values
        ]
        self.required_analysis_data = [
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
        super().__init__(name=name, schema=schema)
        self.assay_schema = assay_schema

        protocol_identifier_schema = _load_schema(
            "", "clinical_trial.json", as_html=False
        )["properties"]["protocol_identifier"]

        # required: List[str] = self.schema["required"]
        for worksheet_name, worksheet_schema in self.schema["properties"][
            "worksheets"
        ].items():
            updates: dict = {}
            preamble_schema: dict = worksheet_schema.get("preamble_rows", {})
            for prop_name, prop_schema in preamble_schema.items():
                data_pointer: str = (
                    "/".join(
                        [
                            self.schema.get("prism_template_root_object_pointer", ""),
                            worksheet_schema.get("prism_preamble_object_pointer", ""),
                        ]
                    )
                    .replace("//", "/")
                    .lstrip("/")
                )
                if isinstance(self.assay_schema, AssaySchema):
                    for prefix in ["assays", "analysis"]:
                        data_pointer = data_pointer.replace(
                            f"{prefix}/{self.assay_schema.name}/",
                            "",
                        ).replace(f"analysis/{self.assay_schema.name}_analysis/", "")
                    if self.assay_schema.name == "clinical":
                        data_pointer = data_pointer.replace("clinical_data", "")
                    elif self.assay_schema.name == "misc":
                        data_pointer = data_pointer.replace(
                            "assays/misc_data", ""
                        ).strip("/")
                    elif self.assay_schema.name == "olink":
                        data_pointer = data_pointer.replace("batches/", "")
                    elif self.assay_schema.name in ("ctdna", "microbiome", "tcr"):
                        data_pointer = data_pointer.replace(
                            f"analysis/{self.assay_schema.name}_analysis/", ""
                        ).replace("batches/", "")
                    elif self.assay_schema.name == "cytof":
                        data_pointer = data_pointer.replace(
                            "cytof_antibodies", "antibodies"
                        )
                    elif self.assay_schema.name == "wes":
                        data_pointer = data_pointer.replace(
                            "analysis/wes_tumor_only_analysis/", ""
                        )

                if "merge_pointer" in prop_schema and prop_schema[
                    "merge_pointer"
                ].endswith("protocol_identifier"):
                    updates[prop_name] = protocol_identifier_schema.copy()

                elif "merge_pointer" in prop_schema:
                    merge_pointer = prop_schema["merge_pointer"].replace("/-", "")

                    levels = merge_pointer.split("/")
                    if levels[0].isdigit() and int(levels[0]):
                        levels = data_pointer.split("/")[: -int(levels[0])] + levels[1:]
                    else:
                        levels = data_pointer.split("/") + levels
                    levels = [l for l in levels if l and l != "-" and not l.isdigit()]

                    if (
                        prop_schema.get("type_ref")
                        and not prop_schema.get("do_not_merge", False)
                        and len(levels)
                    ):
                        context = {levels[0]: {}}
                        if levels[0] in self.assay_schema.assay_metadata:
                            context[levels[0]].update(
                                self.assay_schema.assay_metadata[levels[0]].copy()
                            )
                        if levels[0] in self.assay_schema.analysis_metadata:
                            context[levels[0]].update(
                                self.assay_schema.analysis_metadata[levels[0]].copy()
                            )

                        if not len(context[levels[0]]):
                            raise Exception(
                                f"Cannot find {levels[0]} in {self.assay_schema.name}'s AssaySchema for {prop_name}."
                            )
                    else:
                        context = {}

                    while len(levels) and levels[0] in context:
                        next_level = levels.pop(0)
                        context = context[next_level]

                    if len(levels):
                        raise Exception(
                            f"Cannot find {levels} in {self.assay_schema.name}'s AssaySchema after descending for {prop_name}."
                        )

                    updates[prop_name] = prop_schema.copy()
                    updates[prop_name].update(context)

            if len(updates):
                self.schema["properties"]["worksheets"][worksheet_name][
                    "preamble_rows"
                ].update(updates)

            # macros.properties_table(data)
            data_pointer: str = (
                "/".join(
                    [
                        self.schema.get("prism_template_root_object_pointer", ""),
                        worksheet_schema.get("prism_data_object_pointer", ""),
                    ]
                )
                .replace("//", "/")
                .lstrip("/")
            )

            if isinstance(self.assay_schema, AssaySchema):
                for prefix in ["assays", "analysis"]:
                    data_pointer = data_pointer.replace(
                        f"{prefix}/{self.assay_schema.name}/",
                        "",
                    ).replace(f"analysis/{self.assay_schema.name}_analysis/", "")
                if self.assay_schema.name == "olink":
                    data_pointer = data_pointer.replace("batches/", "")
                elif self.assay_schema.name in ("ctdna", "microbiome", "tcr"):
                    data_pointer = data_pointer.replace(
                        f"analysis/{self.assay_schema.name}_analysis/", ""
                    ).replace("batches/", "")
                elif self.assay_schema.name == "cytof":
                    data_pointer = data_pointer.replace(
                        "cytof_antibodies", "antibodies"
                    )
                elif self.assay_schema.name == "wes":
                    data_pointer = data_pointer.replace(
                        "analysis/wes_tumor_only_analysis/", ""
                    )

            for table_name, table_schema in worksheet_schema.get(
                "data_columns", {}
            ).items():
                # macros.properties_table(table_schema, required)
                updates: dict = {}
                # also table_schema["properties"].items()
                # but none for templates
                for prop_name, prop_schema in table_schema.items():
                    if "merge_pointer" in prop_schema:
                        merge_pointer = prop_schema["merge_pointer"].replace("/-", "")
                        levels = merge_pointer.split("/")
                        if levels[0].isdigit() and int(levels[0]):
                            levels = (
                                data_pointer.split("/")[: -int(levels[0])] + levels[1:]
                            )
                        else:
                            levels = data_pointer.split("/") + levels
                        levels = [
                            l for l in levels if l and l != "-" and not l.isdigit()
                        ]

                        # prop_required: bool = prop_name in required
                        if (
                            prop_schema.get("type_ref")
                            and not prop_schema.get("do_not_merge", False)
                            and len(levels)
                        ):
                            context = {levels[0]: {}}
                            if levels[0] in self.assay_schema.assay_data:
                                context[levels[0]].update(
                                    self.assay_schema.assay_data[levels[0]].copy()
                                )
                            if levels[0] in self.assay_schema.analysis_data:
                                context[levels[0]].update(
                                    self.assay_schema.analysis_data[levels[0]].copy()
                                )

                            if not len(context[levels[0]]):
                                raise Exception(
                                    f"Cannot find {levels[0]} in {self.assay_schema.name}'s AssaySchema for {prop_name}."
                                )
                        else:
                            context = {}

                        while len(levels) and levels[0] in context:
                            next_level = levels.pop(0)
                            context = context[next_level]

                        if len(levels):
                            raise Exception(
                                f"Cannot find {levels} in {self.assay_schema.name}'s AssaySchema after descending for {prop_name}."
                            )

                        updates[prop_name] = prop_schema.copy()
                        updates[prop_name].update(context)

                    if "process_as" in prop_schema:
                        process_as = {}

                        updates[prop_name] = prop_schema.copy()
                        for entry in prop_schema["process_as"]:
                            process_as.update(
                                self._handle_process_as(
                                    prop_name, entry, data_pointer, assay_schema
                                )
                            )
                        updates[prop_name]["process_as"] = process_as

                if len(updates):
                    self.schema["properties"]["worksheets"][worksheet_name][
                        "data_columns"
                    ][table_name].update(updates)


# ----- Utility Functions ----- #
def _load_schema(root: str, path: str, as_html: bool = True) -> dict:
    schema_path = os.path.join(root, path)

    if not as_html:
        # when loading, always in reference to base dir
        return _load_dont_validate_schema(schema_path, SCHEMA_DIR)
    else:

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
        return _load_dont_validate_schema(
            schema_path, SCHEMA_DIR, on_refs=_json_to_html
        )


def _make_file(
    template: jinja2.Template, out_directory: str, scope: str, name: str, schema: dict
):
    full_name = f"{scope}.{name}"
    if full_name.startswith("."):
        full_name = full_name[1::]

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
    schema_dir: str = SCHEMA_DIR, recursive: bool = True, as_html: bool = True
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
def load_files_schemas() -> Dict[str, Dict[str, dict]]:
    ret = load_schemas(schema_dir=os.path.join(SCHEMA_DIR, "artifacts"))[""]
    ret = {k.replace("artifact_", ""): v for k, v in ret.items()}
    return {"files": ret}


def load_assay_schemas() -> Dict[str, Dict[str, dict]]:
    """
    Load all assay template JSON schemas into a dictionary with key "assays"
    and value is an AssaySchema with the related template schemas and assay description.
    """
    # load assay and analysis schemas
    assay_template_schemas = load_schemas(
        schema_dir=os.path.join(SCHEMA_DIR, "templates", "assays"), as_html=False
    )[""]
    analysis_template_schemas = load_schemas(
        schema_dir=os.path.join(SCHEMA_DIR, "templates", "analyses"), as_html=False
    )[""]

    # get generic assay categories
    assay_names = set(
        template_name.split("_")[0] for template_name in assay_template_schemas.keys()
    )

    # load assay descriptions
    all_assay_schemas = load_schemas(
        schema_dir=os.path.join(SCHEMA_DIR, "assays"), recursive=False, as_html=False
    )[""]
    assay_schemas = {
        name.split("_")[0]: schema
        for name, schema in all_assay_schemas.items()
        if name.split("_")[-1] in ("assay", "data")
        and name.split("_")[0] in assay_names
    }
    # clinical is a top level
    assay_schemas["clinical"] = load_schemas(recursive=False, as_html=False)[""][
        "clinical_data"
    ]

    # set up doc configs for each assay
    template_schemas_by_assay = {
        assay_name: AssaySchema(
            name=assay_name,
            schema=assay_schemas[assay_name],
            assays={
                entity_name: entity_schema
                for entity_name, entity_schema in assay_template_schemas.items()
                if entity_name.split("_")[0] == assay_name
            },
            analyses={
                entity_name: schema_tuple
                for entity_name, schema_tuple in analysis_template_schemas.items()
                if entity_name.split("_")[0] == assay_name
            },
        )
        for assay_name in sorted(assay_names)
    }

    return {"assays": template_schemas_by_assay}


def load_manifest_schemas() -> Dict[str, Dict[str, dict]]:
    """
    Load all manifest template JSON schemas into a dictionary with key "manifests"
    and value is dict mapping entity names to the validated schema.
    """
    ret = load_schemas(schema_dir=os.path.join(SCHEMA_DIR, "templates", "manifests"))[
        ""
    ]
    clinical_trial_schema = _load_dont_validate_schema("clinical_trial.json")
    return {
        # # as keys are in relation to schema_dir, add a key before returning
        # "manifests": {
        #     k: TemplateSchema(name=k, schema=v, assay_schema=clinical_trial_schema)
        #     for k, v in ret.items()
        # }
    }


def load_toplevel_schemas(
    keys: List[str] = ["clinical_trial", "participant", "sample"],
) -> Dict[str, Dict[str, dict]]:
    """
    Load just the schemas in SCHEMA_DIR into a dictionary with key ""
    and value is dict mapping entity names to the validated schema.
    """
    # only get the first level of schemas, with key == ""
    ret = load_schemas(schema_dir=SCHEMA_DIR, recursive=False)
    # only keep the ones we"ve specified
    ret[""] = {k: v for k, v in ret[""].items() if k in keys}
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
    schemas_groups.update(load_toplevel_schemas())
    schemas_groups.update(load_assay_schemas())
    schemas_groups.update(load_manifest_schemas())

    index_template = templateEnv.get_template("index.j2")
    index_html = index_template.render(schema_groups=schemas_groups)
    with open(os.path.join(out_directory, "index.html"), "w") as f:
        f.write(index_html)

    # Load all of the different template types to choose from later
    assay_template = templateEnv.get_template("assay.j2")
    entity_template = templateEnv.get_template("entity.j2")
    template_template = templateEnv.get_template("template.j2")

    for scope, entity in schemas_groups.items():
        # Determine whether these are assays, templates, or normal entities
        if scope == "assays":
            template = assay_template
        elif scope:
            template = template_template
        else:
            template = entity_template

        # Generate the html files
        for name, schema in entity.items():
            _make_file(template, out_directory, scope, name, schema)

    # Generate templates for each assay as well
    for assay_name, assay_schema in schemas_groups["assays"].items():
        scope = f"assays.{assay_name}"

        for upload_name, upload_schema in list(assay_schema.assays.items()) + list(
            assay_schema.analyses.items()
        ):
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

    # Generate templates for each artifact
    for scope, file_schemas in load_files_schemas().items():
        for name, schema in file_schemas.items():
            _make_file(entity_template, out_directory, scope, name, schema)


if __name__ == "__main__":
    generate_docs()
