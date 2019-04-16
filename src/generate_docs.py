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
def process(entity_name, templateEnv):
    file_name = "schemas/%s.yaml" % entity_name
    current_yaml = get_yaml(file_name)    

    properties = current_yaml["properties"]
    enum_dict = get_enum_dict(properties)
    sorted_property_list = sorted(properties)

    template = templateEnv.get_template("entity.html")
    outputText = template.render(current_yaml=current_yaml,
        properties=properties,
        sorted_property_list=sorted_property_list,
        enum_dict=enum_dict)
    print ("Creating:  out/%s.html" % entity_name)
    fd = open("out/%s.html" % entity_name, "w")
    fd.write(outputText)
    fd.close()

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

for entity in entity_list:
    process(entity, templateEnv)

# Create the Index Page
template = templateEnv.get_template("index.html")
print ("Creating out/index.html")
outputText = template.render(entity_list=entity_list)
fd = open("out/index.html", "w")
fd.write(outputText)
fd.close()
