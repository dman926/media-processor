# Media Processor

UNDER CONSTRUCTION. PLEASE WAIT FOR RELEASE UNLESS YOU WANT TO FIDDLE WITH IT.

A python program to scan, auto-transcode, rename, and move media.

This was made for my PleX server so I can easily set up rules to automate my workflow.

## Dependencies

* `thefuzz` (for fuzzy search)
* `python-Levenshtein` (to speed up thefuzz)

## Install

* Download repository to your destination
* Run install.sh to create the virtual environment and install dependencies (requires python3-venv) (Windows bat installer coming soon, don't have a Windows PC available to test)
* All files outside of media-processor can be safely deleted

## Run

With virtual environment activated or python3 binary used directly:

* Run main program with `$ python3 media-processor/main.py`. See available flags with `$ python3 media-processor/main.py (-h || --help)`. Shutdown with `CTRL+C` or stopping the service, interrupt is handled.
* Run configurator shell with `$ python3 media-processor/configure.py`. The same shell is opened by `main.py`, but if you are running it as a service, you won't have access to it, so `configure.py` can be run separately to add properties and patterns. See available flags with `$ python3 media-processor/configure.py (-h || --help)`. Additional `exit` command to exit shell is available.

## Available Shell Commands

* `commit` - Commit transaction.
* `vacuum` - Prune the DB to save space.
* `add ...`
  * `property <PROPERTY>` - Add a property.
  * `pattern <PROPERTY> <PATTERN>` - Add a regex pattern to a property for matching.
* `remove`
  * `property <PROPERTY>` - Remove a property.
  * `pattern <PROPERTY>` - Remove a regex pattern from a property.
* `reset`
  * `db` - Clear all data from the DB's tables.
  * `properties` - Clear all data from the `properties` table.
  * `patterns` - Clear all data from the `patterns` table.
