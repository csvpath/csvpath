#!/bin/sh
#
# this script goes in the scripts directory within a csvpath project.
# it must match the [sftpplus] scripts_dir key in config/config.ini.
#
# in this case the csvpath project is named csvpath_sftpplus, but you
# can name it anything you like, as long as you keep this script and
# the scripts_dir key in the sftpplus-side config/config.ini in sync.
#
cd /opt/sftpplus/run/csvpath_sftpplus
echo "$1"
sudo /root/.local/bin/poetry run python ./message_handler.py "$1"



