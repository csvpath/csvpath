CSVPATH_CONFIG_PATH="assets/config/jenkins-local-gcs.ini"
echo $CSVPATH_CONFIG_PATH
whoami
source ~/dev/exports.sh
echo $GCS_CREDENTIALS_PATH
poetry install
poetry run pytest


