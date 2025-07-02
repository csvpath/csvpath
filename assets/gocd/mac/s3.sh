CSVPATH_CONFIG_PATH="assets/config/jenkins-local-s3.ini"
echo $CSVPATH_CONFIG_PATH
source ~/dev/exports.sh
whoami
echo $GCS_CREDENTIALS_PATH
poetry install
poetry run pytest


