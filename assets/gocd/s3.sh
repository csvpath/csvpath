#!/bin/sh
CSVPATH_CONFIG_PATH="assets/config/jenkins-s3.ini"
echo $CSVPATH_CONFIG_PATH
poetry install
poetry run pytest


