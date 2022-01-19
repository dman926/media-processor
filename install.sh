#!/bin/bash

# Create virtual environment and install dependencies

echo "Creating virtual environment (media-processor/venv)"
python3 -m venv media-processor/venv
echo "Created virtual environment"
echo "Installing wheel"
media-processor/venv/bin/pip3 install wheel
echo "Installing pip dependencies..."
media-processor/venv/bin/pip3 install -r media-processor/requirements.txt
echo "Installed. You can start using Media Processor!"