# Change Log

## [Unreleased]
### Added
- CHANGELOG.md
- SDSSconnect added to Totoro root
- EUPS
- Plugger: offline carts are now given higher cart_order. This is because we
don't want APOGEE to use MaNGA offline carts for co-designed plates, if
possible. When the plugger is running for a MaNGA night offlines carts are
given the highest priority after all scheduled carts. For non-MaNGA nights,
offline carts are given higher priority than any other cart except carts with
plates with incomplete sets.
### Changed
- Totoro moved to its own repo.
- Now uses SDSSconnect for connecting to the DB. Requires passwords to be
defined in .pgpass.
