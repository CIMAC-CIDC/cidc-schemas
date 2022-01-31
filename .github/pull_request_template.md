## What

Describe very concisely what this Pull Request does.

## Why

Describe what motivated this Pull Request and why this was necessary. Link to the relevant JIRA Issue. Ex. Closes CIDC-1086

## How

Describe details of how you implemented the solution, outlining the major steps involved in adding this new feature or fixing this bug. Provide code-snippets if possible, showing example usage.

## Remarks

Add notes on possible known quirks/drawbacks of this solution.

## Checklist

Please include and complete the following checklist. You can mark an item as complete with the `- [x]` prefix:

- [ ] Tests - Added unit tests for new code, regression tests for bugs and updated the integration tests if required
- [ ] Formatting & Linting - `black` and `flake8` have been used to ensure styling guidelines are met
- [ ] Type Annotations - All new code has been type annotated in the function signatures using type hints
- [ ] Docstrings - Docstrings have been provided for functions
- [ ] Documentation - Documentation in [`docs/`](https://github.com/CIMAC-CIDC/cidc-schemas/tree/master/docs) has be regenerated and [README](https://github.com/CIMAC-CIDC/cidc-schemas/blob/master/README.md) and [CHANGELOG](https://github.com/CIMAC-CIDC/cidc-schemas/blob/master/CHANGELOG.md) have been updated to explain major changes & new features
- [ ] Package version - Manually bumped the Schemas package version in [`cidc_schemas/__init__.py`](https://github.com/CIMAC-CIDC/cidc-schemas/blob/master/cidc_schemas/__init__.py#L5)
