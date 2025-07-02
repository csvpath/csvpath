CSVPATH_CONFIG_PATH="assets/config/config.ini"
echo $CSVPATH_CONFIG_PATH
source ~/dev/exports.sh
poetry install
poetry run pytest


