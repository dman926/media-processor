# Media Processor

A python program to scan, auto-transcode, rename, and move media.

This was made for my PleX server so I can easily set up rules to automate my workflow.

I will be recreating this as a web application eventually.

## Dependencies

* `thefuzz` (for fuzzy search)
* `python-Levenshtein` (to speed up thefuzz)
* `paramiko` (to sftp files to remote servers. Not technically needed if everything will be local)

## Install

* Download repository to your destination
* Run install.sh to create the virtual environment and install dependencies (requires python3-venv)
* All files outside of media-processor can be safely deleted

## Run

With virtual environment activated or python3 binary used directly:

* Run main program with `$ python3 media-processor/main.py`. See available flags with `$ python3 media-processor/main.py (-h || --help)`. Shutting down with `exit`, `CTRL+C`, or stopping the service, the interrupt is handled.
* Run configurator shell with `$ python3 media-processor/configure.py`. The same shell is opened by `main.py`, but if you are running it as a service, you won't have access to it, so `configure.py` can be run separately to add properties and patterns. See available flags with `$ python3 media-processor/configure.py (-h || --help)`. A GUI is also provided through the configurator by using the `-g` or `--gui` flag. This disables the shell.

## Available Shell Commands

Commands are saved as a list and exececuted on the `exec` command.

* `exec` - Execute commands.
* `wipe` - Wipe (reset) transaction.
* `exit` - Exit the shell. Be aware that this will stop the program. `CTRL+C` will do the same thing.
* `commit` - Commit transaction.
* `vacuum` - Prune the DB to save space.
* `add ...`
  * `property <PROPERTY>` - Add a property.
  * `setting <PROPERTY> <FFMPEG INPUT ARGS> <FFMPEG OUTPUT ARGS> <OUTPUT CONTAINER> <DESTINATION FOLDER> <DESTINATION SERVER (user@ip:port (port optional)) (optional)>` - Add processing settings to a property for matching.
  * `destination <user@ip:port (port optional)> <PASSWORD (optional if using ssh keys)>` - Add a destination server.
* `remove ...`
  * `property <PROPERTY>` - Remove a property and it's processing settings.
  * `setting <PROPERTY>` - Remove processing settings from a property.
  * `destination <user@ip:port (port optional)>` - Remove a destination server and references to the destination server.
* `reset ...` (all except `db` do not clear any foreign key references (might change later))
  * `db` - Clear all data from the DB's tables.
  * `properties` - Clear all data from the `properties` table.
  * `settings` - Clear all data from the `property_settings` table.
  * `destinations` - Clear all data from the `destinations` table.
