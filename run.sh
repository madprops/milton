#!/usr/bin/env bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
  echo "Setting up virtual environment..."
  python -m venv venv
  venv/bin/pip install -r requirements.txt
  echo "Virtual environment setup complete."
else
  echo "Using existing virtual environment."
fi

# Run the main script
echo "Starting milton..."
venv/bin/python -m milton.main