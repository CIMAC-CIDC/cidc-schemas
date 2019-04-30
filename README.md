# cidc-schemas

This repository contains formal defintions of the CIDC metadata model using [json-schema](https://json-schema.org/) syntax and vocabulary.

## View documentation at https://cimac-cidc.github.io/cidc-schemas/

# Running tests
This repository has unit tests in the *tests* folder. After installing dependencies 
the tests can be run via the command
```bash
py.tests --cache-clear tests
```

# Building documentation
The documentation can be built by running the following command
```bash
python bin/generate_docs.py
```
This will create the html documents in /docs. If the changes are comitted and pushed 
to master this they will be viewable at https://cimac-cidc.github.io/cidc-schemas/

# Create template for manifest

1) clone repository
`git clone THIS-REPO`

2) create virtual environment
```bash
virtualenv ENV-NAME
. ENV-NAME/bin/activate
cd schemas
```

3) install dependencies
```
pip install -r requirements.txt
```

3) Run the script
```
python bin/create_template.py -y manifest/pbmc.yaml -o $PWD
```
