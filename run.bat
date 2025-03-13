@echo off
REM Script to set up a new Python environment for the Hue light show project

REM Create a new virtual environment
python -m venv hue_env

REM Activate the virtual environment
call hue_env\Scripts\activate

REM Install the required packages
pip install flask==2.0.1
pip install werkzeug==2.0.1
pip install flask-socketio==5.1.1
pip install phue==1.1

REM Run the web controller
python hue_web_controller.py

REM Keep the window open
pause