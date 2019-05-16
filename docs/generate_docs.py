import os
import json
import jinja2

DOCS_DIR =os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(DOCS_DIR, '..')
SITE_DIR = os.path.join(DOCS_DIR, "site")

# Get the Specified JSON File
def get_json(file_name):
    with open(file_name, 'r') as stream:
        try:
            json_doc = json.load(stream)
            return (json_doc)
        except json.JSONDecodeError as exc:
            print(exc)

# Extract Properties
def extract_properties(properties, property_dict, required):

    # loop over properties
    for current_property in properties:
        target_property = {}
        target_property["description"] = properties[current_property]["description"].replace("'", "")
        target_property["type"] = properties[current_property]["type"]
        try:
            target_property["format"] = properties[current_property]["format"]
        except KeyError:
            target_property["format"] = ""

        try:    
            if current_property in required:
                required_property = "[Required]"
            else:
                required_property = "[Optional]"
            target_property["required"] = required_property
        except KeyError:
            target_property["required"] = "[Optional]"

        try:
            item_list = properties[current_property]["enum"]
            target_property["enum"] = item_list
        except KeyError:
            try:
                item_list = properties[current_property]["items"]["enum"]
                target_property["enum"] = item_list
            except KeyError:
                target_property["enum"] = []
        property_dict[current_property] = target_property

# Create HTML for the Specified Entity
def processEntity(entity_name, template_env, property_dict):
    file_name = os.path.join(ROOT_DIR, "schemas", "%s.json" % entity_name)
    current_json = get_json(file_name)    

    # find required properties
    req_props = {}
    if 'required' in current_json:
      req_props = current_json['required']

    properties = current_json["properties"]
    extract_properties(properties, property_dict, req_props)
    sorted_property_list = sorted(properties)

    template = template_env.get_template("entity.html")
    output_text = template.render(schema=current_json,
        properties=properties,
        sorted_property_list=sorted_property_list,
        property_dict=property_dict)
    print ("Creating:  %s.html" % entity_name)
    fd = open("%s/%s.html" % (SITE_DIR, entity_name), "w")
    fd.write(output_text)
    fd.close()
    return current_json

# Create HTML for the Specified Manifest
def processManifest(manifest_name, entity_json_set, property_dict, column_descriptions, template_env):
    file_name = os.path.join("manifests", manifest_name, "%s.json" % manifest_name)
    current_json = get_json(file_name)    

    template = template_env.get_template("manifest.html")
    output_text = template.render(schema=current_json,
        entity_json_set=entity_json_set,
        property_dict=property_dict,
        column_descriptions=column_descriptions)
    print ("Creating:  %s.html" % manifest_name)
    fd = open("%s/%s.html" % (SITE_DIR, manifest_name), "w")
    fd.write(output_text)
    fd.close()
    return current_json

def generate_docs():

  templateLoader = jinja2.FileSystemLoader(os.path.join(DOCS_DIR, "templates"))
  templateEnv = jinja2.Environment(loader=templateLoader)
  property_dict = {}

  # Create HTML Pages for Each Entity
  entity_list = []
  entity_list.append("clinical_trial")
  entity_list.append("participant")
  entity_list.append("sample")
  entity_list.append("aliquot")
  entity_list.append("user")
  entity_list.append("artifact")
  entity_list.append("wes_artifact")
  entity_list.append("shipping_core")
  entity_json_set = {}
  for entity in entity_list:
      entity_json_set[entity] = (processEntity(entity, templateEnv, property_dict))

  # Create HTML Pages for Each Manifest
  column_descriptions = {}
  column_descriptions["core_columns"] = "Core Columns:  Manifest Header"
  column_descriptions["shipping_columns"] = "Shipping Columns:  Completed by the BioBank"
  column_descriptions["receiving_columns"] = "Receiving Columns:  Completed by the CIMAC"

  manifest_list = []
  manifest_list.append("pbmc")
  manifest_json_set = {}
  for manifest in manifest_list:
      manifest_json_set[manifest] = processManifest(manifest, entity_json_set,
      property_dict, column_descriptions, templateEnv)

  # Create the Index Page
  template = templateEnv.get_template("index.html")
  print ("Creating index.html")
  outputText = template.render(entity_list=entity_list, entity_json_set=entity_json_set,
      manifest_list=manifest_list, manifest_json_set=manifest_json_set)
  fd = open("%s/index.html" % SITE_DIR, "w")
  fd.write(outputText)
  fd.close()

if __name__ == '__main__':
  generate_docs()