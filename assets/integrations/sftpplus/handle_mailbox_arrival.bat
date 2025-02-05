echo "%1 arrived"

echo ">> moving to the project dir"
cd c:\sftpplus\run\transfers

echo ">> running"

poetry install && poetry run python handle_mailbox_arrival.py "%1"



