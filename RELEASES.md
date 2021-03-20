# Tax-Brain Release History

## 2021-03-19 Release 2.5.0

Last Merged Pull Request: [#165](https://github.com/PSLmodels/Tax-Brain/pull/165)

Note: This will be the first release available on Conda-Forge and the first to support Python 3.8

Changes in this release:

* Fix Compute Studio random seed generation ([#141](https://github.com/PSLmodels/Tax-Brain/pull/141))
* Add LaTex installer to Compute Studio instructions ([#142](https://github.com/PSLmodels/Tax-Brain/pull/142))
* Skip report creation for Compute Studio runs with no reform ([#148](https://github.com/PSLmodels/Tax-Brain/pull/148))
* Add Volcano Plot ([#149](https://github.com/PSLmodels/Tax-Brain/pull/149))
* Add Lorenz Curve Plot ([#150](https://github.com/PSLmodels/Tax-Brain/pull/150))
* Update automated reports ([#151](https://github.com/PSLmodels/Tax-Brain/pull/151))
* Add an option to include a `Total` column in generated tables ([#154](https://github.com/PSLmodels/Tax-Brain/pull/154))
* Update docstrings ([#159](https://github.com/PSLmodels/Tax-Brain/pull/159))
* Add continuous integration and unit testing through GitHub Actions ([#160](https://github.com/PSLmodels/Tax-Brain/pull/160))
* Add revenue plot ([#165](https://github.com/PSLmodels/Tax-Brain/pull/165))

## 2020-10-10 Release 2.4.0

Last Merged Pull Request: [#135](https://github.com/PSLmodels/Tax-Brain/pull/135)

Changes in this release:

* Automated reports are now produced using just Pandoc ([#125](https://github.com/PSLmodels/Tax-Brain/pull/125), [#135](https://github.com/PSLmodels/Tax-Brain/pull/135))

* The Tax-Brain Compute Studio app now includes automated reports in the
downloadable content ([#76](https://github.com/PSLmodels/Tax-Brain/pull/76))

* Tax-Brain now requires `taxcalc` version 3.0.0 or above and `behresp` 0.11.0 or above ([#128](https://github.com/PSLmodels/Tax-Brain/pull/128))

* All images used in producing automated reports are now made with `matplotlib`, greatly reducing the number of external projects we need to install ([#134](https://github.com/PSLmodels/Tax-Brain/pull/134))


## 2020-07-07 Release 2.3.4

Last Merged Pull Request: [#124](https://github.com/PSLmodels/Tax-Brain/pull/124)

No changes made to the model between release 2.3.3 and 2.3.4. The only changes
were to the conda build instructions.

## 2020-07-06 Release 2.3.3

Last Merged Pull Request [#123](https://github.com/PSLmodels/Tax-Brain/pull/123)

Changes in this release:

* Fixes various Compute Studio bugs (
  [#78](https://github.com/PSLmodels/Tax-Brain/pull/78),
  [#82](https://github.com/PSLmodels/Tax-Brain/pull/82),
  [#83](https://github.com/PSLmodels/Tax-Brain/pull/83)
)
* Update installation requirements (
  [#80](https://github.com/PSLmodels/Tax-Brain/pull/80),
  [#81](https://github.com/PSLmodels/Tax-Brain/pull/81),
  [#84](https://github.com/PSLmodels/Tax-Brain/pull/84),
  [#90](https://github.com/PSLmodels/Tax-Brain/pull/90),
  [#91](https://github.com/PSLmodels/Tax-Brain/pull/91)
)
* Add Compute Studio Documentation (
  [#87](https://github.com/PSLmodels/Tax-Brain/pull/87),
  [#92](https://github.com/PSLmodels/Tax-Brain/pull/92)
)
* Compute Studio updates (
  [#88](https://github.com/PSLmodels/Tax-Brain/pull/88),
  [#89](https://github.com/PSLmodels/Tax-Brain/pull/89),
  [#103](https://github.com/PSLmodels/Tax-Brain/pull/103),
  [#108](https://github.com/PSLmodels/Tax-Brain/pull/108),
  [#109](https://github.com/PSLmodels/Tax-Brain/pull/109),
  [#111](https://github.com/PSLmodels/Tax-Brain/pull/111),
  [#112](https://github.com/PSLmodels/Tax-Brain/pull/112),
  [#118](https://github.com/PSLmodels/Tax-Brain/pull/118),
)
* Fix handling of baseline policy in the core taxbrain app
([#93](https://github.com/PSLmodels/Tax-Brain/pull/93))
* Update core taxbrain app to use Bokeh version 2.0.0 and Tax-Calculator 2.9.0
([#113](https://github.com/PSLmodels/Tax-Brain/pull/113))
* Add benefits totals to aggregate table
([#120](https://github.com/PSLmodels/Tax-Brain/pull/118))
* Update the report feature of the core taxbrain app to only use PNGs for graphs
[#123](https://github.com/PSLmodels/Tax-Brain/pull/123)

## 2019-07-30 Release 2.3.2

Last Merged Pull Request: [#74](https://github.com/PSLmodels/Tax-Brain/pull/74)

No changes made to the model between release 2.3.1 and 2.3.2. The only changes
were to the conda build instructions.

## 2019-07-29 Release 2.3.1

Last Merged Pull Request: [#73](https://github.com/PSLmodels/Tax-Brain/pull/73)

No changes made to the model between release 2.3.0 and 2.3.1. The only changes
were to the conda build instructions.

## 2019-07-24 Release 2.3.0

Last Merged Pull Request: [#72](https://github.com/PSLmodels/Tax-Brain/pull/72)

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
* Add automated report capabilities ([#69](https://github.com/PSLmodels/Tax-Brain/pull/69))

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
