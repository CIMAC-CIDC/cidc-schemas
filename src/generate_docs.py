import yaml
import jinja2

# Get the Specified YAML File
def get_yaml(file_name):
    with open(file_name, 'r') as stream:
        try:
            yaml_doc = yaml.safe_load(stream)
            return (yaml_doc)
        except yaml.YAMLError as exc:
            print(exc)

# Extract Enum Lists
def get_enum_dict(properties):
    enum_dict = {}
    for current_property in properties:
        try:
            item_list = properties[current_property]["enum"]
            enum_dict[current_property] = item_list
        except KeyError:
            try:
                item_list = properties[current_property]["items"]["enum"]
                enum_dict[current_property] = item_list
            except KeyError:
                enum_dict[current_property] = []
    return enum_dict

# Create HTML for the Specified Entity
def processEntity(entity_name, template_env):
    file_name = "schemas/%s.yaml" % entity_name
    current_yaml = get_yaml(file_name)    

    properties = current_yaml["properties"]
    enum_dict = get_enum_dict(properties)
    sorted_property_list = sorted(properties)

    template = template_env.get_template("entity.html")
    output_text = template.render(current_yaml=current_yaml,
        properties=properties,
        sorted_property_list=sorted_property_list,
        enum_dict=enum_dict)
    print ("Creating:  out/%s.html" % entity_name)
    fd = open("out/%s.html" % entity_name, "w")
    fd.write(output_text)
    fd.close()
    return current_yaml

# Create HTML for the Specified Manifest
def processManifest(manifest_name, entity_yaml_set, template_env):
    file_name = "manifests/%s.yaml" % manifest_name
    current_yaml = get_yaml(file_name)    

    template = template_env.get_template("manifest.html")
    output_text = template.render(current_yaml=current_yaml,
        entity_yaml_set=entity_yaml_set)
    print ("Creating:  out/%s.html" % manifest_name)
    fd = open("out/%s.html" % manifest_name, "w")
    fd.write(output_text)
    fd.close()
    return current_yaml

templateLoader = jinja2.FileSystemLoader(searchpath="templates/")
templateEnv = jinja2.Environment(loader=templateLoader)

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
    entity_yaml_set[entity] = (processEntity(entity, templateEnv))

# Create HTML Pages for Each Manifest
manifest_list = []
manifest_list.append("pbmc")
manifest_yaml_set = {}
for manifest in manifest_list:
    manifest_yaml_set[manifest] = processManifest(manifest, entity_yaml_set, templateEnv)

# Create the Index Page
template = templateEnv.get_template("index.html")
print ("Creating out/index.html")
outputText = template.render(entity_list=entity_list, entity_yaml_set=entity_yaml_set,
    manifest_list=manifest_list, manifest_yaml_set=manifest_yaml_set)
fd = open("out/index.html", "w")
fd.write(outputText)
fd.close()
