#!/bin/sh

# Run manage.py to create database tables
python manage.py

# Start Flask using the flask run command
flask run --host 0.0.0.0 --port 8001 --reload --debug
