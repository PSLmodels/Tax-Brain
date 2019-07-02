# Tax-Brain Release History

## 2019-xx-xx Release x.x.x

Last Merged Pull Request: [#68](https://github.com/PSLmodels/Tax-Brain/pull/68)

Changes in this release:

* Refactor the `run()` method and TaxBrain initialization process so that
  calculator objects are not created until `run()` is called ([#44](https://github.com/PSLmodels/Tax-Brain/pull/44))
* Modify `metaparams` in the `COMPconfig` ([#54](https://github.com/PSLmodels/Tax-Brain/pull/54))
* Fix various COMP bugs ([#58](https://github.com/PSLmodels/Tax-Brain/pull/58),
  [#60](https://github.com/PSLmodels/Tax-Brain/pull/60),
  [#63](https://github.com/PSLmodels/Tax-Brain/pull/63),
  [#65](https://github.com/PSLmodels/Tax-Brain/pull/65))
* Allow users to specify an alternative policy to use as the baseline, rather
  than current law ([#64](https://github.com/PSLmodels/Tax-Brain/pull/64))
* Update COMP table outputs so they are more readable ([#66](https://github.com/PSLmodels/Tax-Brain/pull/66))
* Add TaxBrain command line interface ([#67](https://github.com/PSLmodels/Tax-Brain/pull/67), [#68](https://github.com/PSLmodels/Tax-Brain/pull/68))

## 2019-05-24 Release 2.2.1

Last Merged Pull Request: [#51](https://github.com/PSLmodels/Tax-Brain/pull/51)

Changes in this release:

* Fix bug in COMP outputs that caused the rows in distribution tables to be
  flipped ([#51](https://github.com/PSLmodels/Tax-Brain/pull/51)).
* Update Behavioral-Responses package requirements ([#50](https://github.com/PSLmodels/Tax-Brain/pull/50)).
* Change the dynamic reform to run sequentially, rather than in parallel ([#50](https://github.com/PSLmodels/Tax-Brain/pull/50)).

## 2019-05-21 Release 2.2.0

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