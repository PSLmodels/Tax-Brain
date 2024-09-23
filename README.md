| | |
| --- | --- |
| Org | [![PSL cataloged](https://img.shields.io/badge/PSL-cataloged-a0a0a0.svg)](https://www.PSLmodels.org) [![OS License: CCO-1.0](https://img.shields.io/badge/OS%20License-CCO%201.0-yellow)](https://github.com/PSLmodels/Tax-Brain/blob/master/LICENSE) [![Jupyter Book Badge](https://jupyterbook.org/badge.svg)](https://pslmodels.github.io/Tax-Brain/) |
| Package | [![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3108/)  [![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3118/) [![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3121/) [![PyPI Latest Release](https://img.shields.io/pypi/v/taxbrain.svg)](https://pypi.org/project/taxbrain/) [![PyPI Downloads](https://img.shields.io/pypi/dm/taxbrain.svg?label=PyPI%20downloads)](https://pypi.org/project/taxbrain/) [![Anaconda](https://img.shields.io/conda/dn/conda-forge/taxbrain?color=brightgreen&label=downloads&logo=conda-forge)](https://anaconda.org/conda-forge/taxbrain)|
| Testing | ![example event parameter](https://github.com/PSLmodels/Tax-Brain/actions/workflows/build_and_test.yml/badge.svg?branch=master) ![example event parameter](https://github.com/PSLmodels/Tax-Brain/actions/workflows/deploy_jupyterbook.yml/badge.svg?branch=master)  [![Codecov](https://codecov.io/gh/PSLmodels/Tax-Brain/branch/master/graph/badge.svg)](https://codecov.io/gh/PSLmodels/Tax-Brain) |

Tax-Brain
==============

Tax-Brain is a Python package that wraps two models, [Tax-Calculator](https://taxcalc.pslmodels.org) and [Behavioral Responses](https://github.com/PSLmodels/Behavioral-Responses), in one easy
to use interface for producing revenue estimates and distributional analysis of tax policy changes.

We are seeking contributors and maintainers. If you are interested in joining the project as a contributor or maintainer,
open a new [issue](https://github.com/PSLmodels/Tax-Calculator/issues) and ping [@jdebacker](https://github.com/jdebacker/) -- or just jump right in.

Complete documentation is available at
[`taxbrain.pslmodels.org`](http://taxbrain.pslmodels.org/content/intro.html).

## Overview

Tax-Brain makes it easy for users to simulate the US tax system by providing a
single interface for multiple tax models. Currently, Tax-Brain interfaces with
[Tax-Calculator](https://github.com/PSLmodels/Tax-Calculator) and
[Behavioral-Responses](https://github.com/PSLmodels/Behavioral-Responses).
Additional models will be added in the near future to expand Tax-Brain's
capabilities to include modeling business taxation and running dynamic
general equilibrium simulations.

To learn more about how Tax-Brain works, see [the Tax-Brain documentation](http://taxbrain.pslmodels.org).

## Disclaimer

Tax-brain and its underlying models are constantly being improved upon. For
that reason, the results output by Tax-Brain may differ over time. It is
strongly suggested that the user make note of which version of Tax-Brain,
they are using when reporting their results.

## Installing Tax-Brain

You can install the latest official release from PyPI using this command:
`pip taxbrain`.

Similarly, you can update to the latest release of Tax-Brain using
`pip install -U taxbrain`.

Tax-Brain is no longer maintained on Conda.

## Using Tax-Brain

View the sample code in [example.py]([example.py](http://taxbrain.pslmodels.org/content/examples/example.html)) to see how to run Tax-Brain.
Or, see [the user guide](http://taxbrain.pslmodels.org/content/usage.html)
for a more detailed walk through.

## Citing Tax-Brain

Please cite the source of your analysis as "Tax-Brain release #.#.#, author's
calculations." If you would like to link to Tax-Brain, please use
`https://github.com/PSLmodels/Tax-Brain`. It is also strongly suggested that
you describe your input data and note the versions of the underlying models.

## Tax-Brain Interface

In addition to its Python API, Tax-Brain has also been used to power web applications on
[Compute Studio](https://compute.studio/) and other platforms. An application used to be available at
[here](https://compute.studio/PSLmodels/Tax-Brain/). The code behind the
GUI web application can be found in this repository in the [cs-config](https://github.com/PSLmodels/Tax-Brain/tree/master/cs-config)
directory.

## Additional Information

* [Project Road Map](https://github.com/PSLmodels/Tax-Brain/blob/master/ROADMAP.md)
* [Contributing](http://taxbrain.pslmodels.org/content/contributing/contributor_guide.html)
* [Contributors](https://github.com/PSLmodels/Tax-Brain/graphs/contributors)
* [Release History](https://github.com/PSLmodels/Tax-Brain/blob/master/RELEASES.md)

