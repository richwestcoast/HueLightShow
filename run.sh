#!/bin/bash
# Script to set up a new Python environment for the Hue light show project

# Create a new virtual environment
python -m venv hue_env

# Activate the virtual environment
# On Windows:
# hue_env\Scripts\activate
# On macOS/Linux:
source hue_env/bin/activate

# Install the required packages
pip install flask==2.0.1
pip install werkzeug==2.0.1
pip install flask-socketio==5.1.1
pip install phue==1.1

# Run the web controller
python hue_web_controller.py