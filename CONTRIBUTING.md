# Contributing to Tax-Brain

Contributions to Tax-Brain are always welcome. To contribute, open a
[pull request (PR)](https://github.com/PSLmodels/Tax-Brain/pulls) with your changes
and any associated tests. In this PR, please describe what your change does and
link to any relevant issues and discussions.

## Feature Requests

To request a feature, please open an [issue](https://github.com/PSLmodels/Tax-Brain/issues)
describing the desired feature and it's use cases.

## Bug Reports

To report a bug in Tax-Brain, open an [issue](https://github.com/PSLmodels/Tax-Brain/issues)
describing the bug. Please include the code needed to reproduce the bug.

## Developer Setup

Start by forking and cloning the Tax-Brain repo. Next, run the following commands
in the terminal to create and activate the developer conda environment:

```bash
cd Tax-Brain
conda env create -f environment.yml
conda activate taxbrain-dev
```

## Testing

Once you've made your changes, you can test them by running the command
`pytest` in the terminal window. If you do not have access to the `puf.csv`
file, run `pytest -m "not requires_puf` instead.