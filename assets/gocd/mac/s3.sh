CSVPATH_CONFIG_PATH="assets/config/jenkins-local-s3.ini"
echo $CSVPATH_CONFIG_PATH
. ~/dev/exports.sh
poetry install
poetry run pytest


