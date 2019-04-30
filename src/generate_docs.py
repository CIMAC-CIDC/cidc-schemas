import yaml
import jinja2

DOC_DIR = "docs"

# Get the Specified YAML File
def get_yaml(file_name):
    with open(file_name, 'r') as stream:
        try:
            yaml_doc = yaml.safe_load(stream)
            return (yaml_doc)
        except yaml.YAMLError as exc:
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
    file_name = "schemas/%s.yaml" % entity_name
    current_yaml = get_yaml(file_name)    

    # find required properties
    req_props = {}
    if 'required' in current_yaml:
      req_props = current_yaml['required']

    properties = current_yaml["properties"]
    extract_properties(properties, property_dict, req_props)
    sorted_property_list = sorted(properties)

    template = template_env.get_template("entity.html")
    output_text = template.render(current_yaml=current_yaml,
        properties=properties,
        sorted_property_list=sorted_property_list,
        property_dict=property_dict)
    print ("Creating:  %s.html" % entity_name)
    fd = open("%s/%s.html" % (DOC_DIR, entity_name), "w")
    fd.write(output_text)
    fd.close()
    return current_yaml

# Create HTML for the Specified Manifest
def processManifest(manifest_name, entity_yaml_set, property_dict, column_descriptions, template_env):
    file_name = "manifests/%s.yaml" % manifest_name
    current_yaml = get_yaml(file_name)    

    template = template_env.get_template("manifest.html")
    output_text = template.render(current_yaml=current_yaml,
        entity_yaml_set=entity_yaml_set,
        property_dict=property_dict,
        column_descriptions=column_descriptions)
    print ("Creating:  %s.html" % manifest_name)
    fd = open("%s/%s.html" % (DOC_DIR, manifest_name), "w")
    fd.write(output_text)
    fd.close()
    return current_yaml

def generate_docs():

  templateLoader = jinja2.FileSystemLoader(searchpath="templates/")
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
  entity_yaml_set = {}
  for entity in entity_list:
      entity_yaml_set[entity] = (processEntity(entity, templateEnv, property_dict))

  # Create HTML Pages for Each Manifest
  column_descriptions = {}
  column_descriptions["core_columns"] = "Core Columns:  Manifest Header"
  column_descriptions["shipping_columns"] = "Shipping Columns:  Completed by the BioBank"
  column_descriptions["receiving_columns"] = "Receiving Columns:  Completed by the CIMAC"

  manifest_list = []
  manifest_list.append("pbmc")
  manifest_yaml_set = {}
  for manifest in manifest_list:
      manifest_yaml_set[manifest] = processManifest(manifest, entity_yaml_set,
      property_dict, column_descriptions, templateEnv)

  # Create the Index Page
  template = templateEnv.get_template("index.html")
  print ("Creating index.html")
  outputText = template.render(entity_list=entity_list, entity_yaml_set=entity_yaml_set,
      manifest_list=manifest_list, manifest_yaml_set=manifest_yaml_set)
  fd = open("%s/index.html" % DOC_DIR, "w")
  fd.write(outputText)
  fd.close()

if __name__ == '__main__':
  generate_docs()