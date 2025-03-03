#!/bin/zsh

# Path to your virtual environment
VENV_PATH="/Users/levirogalla/Projects/lib/ai-resume-builder/env"

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Run the Python script with arguments
python3 /Users/levirogalla/Projects/lib/ai-resume-builder/src/cli.py "$@"

# Deactivate the virtual environment
deactivate