# Media Processor

UNDER CONSTRUCTION. PLEASE WAIT FOR RELEASE UNLESS YOU WANT TO FIDDLE WITH IT.

A python program to scan, auto-transcode, rename, and move media.

This was made for my PleX server so I can easily set up rules to automate my workflow.

## Install

* Download repository to your destination
* Run install.sh to create the virtual environment and install dependencies (requires python3-venv) (Windows bat installer coming soon, don't have a Windows PC available to test)
* All files outside of media-processor can be safely deleted

## Run

With virtual environment activated or python3 binary used directly:

* Run main program with `$ python3 media-processor/main.py`. See available flags with `$ python3 media-processor/main.py (-h || --help)`.
* Run configurator shell with `$ python3 media-processor/configure.py`.  See available flags with `$ python3 media-processor/configure.py (-h || --help)`.