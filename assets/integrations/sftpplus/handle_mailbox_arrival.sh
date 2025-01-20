#!/bin/bash
echo "arrived! $1"

echo ">> who am I?"
whoami
echo ">> where am I?"
pwd

echo ">> moving to the project dir"
cd run/transfers

echo ">> running"

/Users/sftpplus/.local/bin/poetry install && /Users/sftpplus/.local/bin/poetry run python handle_mailbox_arrival.py "$1"


