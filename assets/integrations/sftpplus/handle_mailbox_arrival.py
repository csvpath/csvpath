import sys
import json
from csvpath.managers.integrations.sftpplus.transfer_creator import (
    SftpPlusTransferCreator,
)

if __name__ == "__main__":
    path = sys.argv[1]
    print(f">>> handle_arrival.py: main: path: {path}")

    arrival = SftpPlusTransferCreator(path)
    print(f">>> arrival: {arrival}")
    arrival.process_message()
