CSVPATH_CONFIG_PATH="assets/config/jenkins-local-azure.ini"
echo $CSVPATH_CONFIG_PATH
source ~/dev/exports.sh
poetry install -E
poetry run pytest


