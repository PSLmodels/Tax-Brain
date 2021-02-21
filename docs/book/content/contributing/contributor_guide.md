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

## Releasing a new version

We use [`Package Builder`](https://github.com/PSLmodels/Package-Builder) to 
release new versions of Tax-Brain and upload them to the [pslmodels channel](https://anaconda.org/pslmodels)
on Anaconda Cloud. To set up your environment for 
installation, run these commands:

```bash
$ conda install -c PSLmodels pkgbld --yes
$ conda config --add channels conda-forge
```

Once you've done that, you can build the package locally to test that everything
workds correctly using:

```bash
$ cd Tax-Brain
$ pbrelease Tax-Brain taxbrain 0.0.0 --local
```

If all goes well, uninstall the local package that was just created

```bash
$ conda uninstall taxbrain --yes
```
And then execute this command

```bash
$ pbrelease Tax-Brain taxbrain X.X.X
```
Where `X.X.X` is the release version.