# Change Log

## [1.7.0] - 2016-06-09
### Changed
- Improved efficiency in loading many plates by optimising queries and
lazy loading all information during the initialisation of Plate and Exposure.


## [1.6.2] - 2016-04-07
### Fixed
- A bug that gives higher priority to not started vs started plates when they
both are completed during the plugging/planning simulation


## [1.6.1] - ???
### Changed
- ???


## [1.6] - ???
### Changed
- ???


## [1.5.4] - ???
### Changed
- Updated default goodWeatherFraction to 0.5.


## [1.5.3] - 2016-01-19
### Changed
- Modified simulation efficiencies to 0.755 (to avoid problems with three exps.
not making the 1-hour window).


## [1.5.2] - 2016-01-18
### Added
- Initial buffer for plugger. If the observing block is in the second part of
the night, the scheduling starts defaults.plugger.initialBufferMin before the
official schedule time. Issues a series of warnings. If Plugger is called with
the keyword useInitialBuffer=False, the initial buffer is not applied. Right
now all plugger tests use this option to avoid changing the results. This
should be fixed eventually.


## [1.5.1] - 2016-01-12
### Fixed
- Fixed a bad keyword in the set rearrangement script that made it fail.
### Refactored
- Improved get plates function.


## [1.5] - 2015-12-12
### Fixed
- Plate.addMockExposure only rearranges exposures in complete sets if the
number of such exposures in the plate is <= 5. Otherwise, it can cause serious
delays for plugging.
### Refactored
- Major refactoring and documenting of plate_utils, scheduler_utils, planner,
and plugger.
- Most classes and functions in dbclasses can now be also accessed from the
root of the module.


## [1.2.1] - 2015-11-13
### Added
- runTests.py now restores, if possible, the test DB before running. If the
script is called with '--no-restore' it will skip the restoration.
### Fixed
- Fixed a bug in the plugging logic that would chose a plate for a single
exposure when another started plate was available for that same LST window, but
had lower increase in SN2. The code now looks for plates that already have
signal (either real or simulated) and prioritises those.


## [1.2.0] - 2015-11-10
### Changed
- When adding new exposures found in the DB, Totoro won't try to rearrange the
exposures in incomplete sets to optimise SN2 and patch dithers.
The rearrangement still happens for simulated exposures (plugger and planner).

## [1.1.2] - 2015-11-09
### Changed
- Adds Totoro to the PYTHONPATH when running the rearrangeSets scripts. This
fixes a problem when rearrangeSets is called from Petunia and Totoro is not in
the PYTHONPATH.

## [1.1.1] - 2015-11-09
### Fixed
- Bug in set rearrangement when one or more of the exposures is invalid

## [1.1.0] - 2015-11-08
### Changed
- Seeing for simulated exposures changed from 1 to 1.5 arcsec and set as a
configurable option in defaults.simulation.seeing.
### Fixed
- Plugger: fixes a bug when a plugged plate cannot be observed for an integer
number of sets. In that case, the orphaned exposures are removed and the
remaining time is to be observed with a different plate. However, if there is
no other plate that can be used to observe at least one whole set, the
original, already plugged plate must be favoured.

## [1.0.1] - 2015-11-06
### Added
- New method in Exposure to get the mean airmass during the exposure.
### Changed
- Zenith avoidance set to 5 degrees by default for planner.
### Fixed
- Small bug fixes
- Fixes a bug when there are no exposures to clean in a simulation.

## [1.0.0] - 2015-10-30
### Added
- CHANGELOG.md
- SDSSconnect added to Totoro root
- EUPS
- Plugger: offline carts are now given higher cart_order. This is because we
don't want APOGEE to use MaNGA offline carts for co-designed plates, if
possible. When the plugger is running for a MaNGA night offline carts are
given the highest priority after all scheduled carts. For non-MaNGA nights,
offline carts are given higher priority than any other cart except carts with
plates with incomplete sets.
- Module file
### Changed
- Totoro moved to its own repo.
- scheduler_utils: plates are sorted by completion so that, if several plates
complete with the same number of exposures, the one with highest completion
gets chosen.
- Now uses SDSSconnect for connecting to the DB. Requires passwords to be
defined in .pgpass.
- DB classes now don't inherit from model classes. Instead, the DB query object
is recorded as object.\_dbObject. DB attributes can still be accessed from the
Totoro object via a custom `__getattr__` method.
