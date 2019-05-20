# Tax-Brain

Tax-Brain is a Python package that wraps multiple economic models in one easy
to use interface.

## Overview

Tax-Brain makes it easy for users to simulate the US tax system by providing a
single interface for multiple tax models. Currently, Tax-Brain interfaces with
[Tax-Calculator](https://github.com/PSLmodels/Tax-Calculator) and
[Behavior-Response](https://github.com/PSLmodels/Behavioral-Responses).
Additional models will be added in the near future to expand Tax-Brain's
capabilities to include modeling business taxation and running dynamic
general equilibrium simulations.

To learn more about how Tax-Brain works, see [this](https://github.com/PSLmodels/Tax-Brain/blob/master/DOC.md)
document.

## Disclaimer

Tax-brain and it's underlying models are constantly being improved upon. For
that reason, the results output by Tax-Brain may differ over time. It is
strongly suggested that the user make note of which version of Tax-Brain,
they are using when reporting their results.

## Installing Tax-Brain

You can install the latest official release from Conda using this command:
`conda install -c pslmodels taxbrain`.

Similarly, you can update to the latest release of Tax-Brain using
`conda update -c pslmodels taxbrain`.

Tax-Brain is currently not available on PyPI.

## Using Tax-Brain

View the sample code in [example.py](example.py) to see how to run Tax-Brain.
Or, see [this document](https://github.com/PSLmodels/Tax-Brain/blob/master/USAGE.md)
for a more detailed walk through.

## Citing Tax-Brain

Please cite the source of your analysis as "Tax-Brain release #.#.#, author's
calculations." If you would like to link to Tax-Brain, please use
`https://github.com/PSLmodels/Tax-Brain`. It is also strongly suggested that
you describe your input data and note the versions of the underlying models.

## Tax-Brain Interface

In addition to its Python API, Tax-Brain also powers a web application on
[COMP](https://www.compmodels.org/about/). That application can be found
[here](https://www.compmodels.org/PSLmodels/Tax-Brain/). The code behind the
GUI can be found in this repository in the [compconfig](https://github.com/PSLmodels/Tax-Brain/tree/master/compconfig)
directory.

## Additional Information

* [Project Road Map](https://github.com/PSLmodels/Tax-Brain/blob/master/ROADMAP.md)
* [Contributors](https://github.com/PSLmodels/Tax-Brain/graphs/contributors)
* [Release History](https://github.com/PSLmodels/Tax-Brain/blob/master/RELEASES.md)

***Looking for code powering the TaxBrain GUI at [apps.ospc.org/taxbrain](https://apps.ospc.org/taxbrain)? See [github.com/ospc-org/ospc.org](https://github.com/ospc-org/ospc.org).***
