CSVPATH_CONFIG_PATH="assets/config/jenkins-s3.ini"
echo $CSVPATH_CONFIG_PATH
source ~/dev/exports.sh
poetry install
poetry run pytest


