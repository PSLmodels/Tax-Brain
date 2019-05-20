# Tax-Brain Release History

## 2019-05-20 Release 2.2.0

Last Merged Pull Request: [#45](https://github.com/PSLmodels/Tax-Brain/pull/45)

Changes in this release:

* Fix bug in the distribution table ([#33](https://github.com/PSLmodels/Tax-Brain/pull/33)).
* Expand testing ([#34](https://github.com/PSLmodels/Tax-Brain/pull/45)).
* Remove TBI package from distribution ([#38](https://github.com/PSLmodels/Tax-Brain/pull/38))
* Establish `compconfig` directory to handle COMP interactions ([#38](https://github.com/PSLmodels/Tax-Brain/pull/38), [#40](https://github.com/PSLmodels/Tax-Brain/pull/40)).
* Modify the distribution and difference table creation to work with taxcalc 2.2.0 ([#45](https://github.com/PSLmodels/Tax-Brain/pull/45)).
* Add plotting to COMP outputs ([#26](https://github.com/PSLmodels/Tax-Brain/pull/26)).

## 2019-04-01 Release 2.1.2

Last Merged Pull Request: [#31](https://github.com/PSLmodels/Tax-Brain/pull/31)

Changes in this release:

* Patches bugs in the TBI ([#31](https://github.com/PSLmodels/Tax-Brain/pull/31)).

## 2019-03-29 Release 2.1.1

Last Merged Pull Request: [#29](https://github.com/PSLmodels/Tax-Brain/pull/29)

Changes in this release:

* Includes `taxbrain/tbi/behavior_params.json` in the package ([#29](https://github.com/PSLmodels/Tax-Brain/pull/29)).

## 2019-03-29 Release 2.1.0

Last Merged Pull Request: [#28](https://github.com/PSLmodels/Tax-Brain/pull/27)

Changes in this release:

* The TBI has been refactored to use the `TaxBrain` class rather than the
  individual components of Tax-Calculator and Behavioral-Responses ([#21](https://github.com/PSLmodels/Tax-Brain/pull/21)).
* The `TaxBrain` class and TBI have been updated to work with newer version of
  Tax-Calculator and Behavioral-Responses (>=1.1.0 and >=0.7.0, respectively) ([#25](https://github.com/PSLmodels/Tax-Brain/pull/25)).
* The TBI has been modified to allow a user to use the PUF as an input file ([#27](https://github.com/PSLmodels/Tax-Brain/pull/27)).

## 2019-03-12 Release 2.0.0

Last Merged Pull Request: [#19](https://github.com/PSLmodels/Tax-Brain/pull/19)

This is the first release of the Tax-Brain package. We are starting with version
2.0.0 because this package is effectively the second coming of the original
Tax-Brain - a web interface for the Tax-Calculator model. Accordingly, much
of the code has been copied directly from the original Tax-Brain.