import sys
import json
from csvpath.managers.integrations.sftpplus.arrival_handler import (
    SftpPlusArrivalHandler,
)

if __name__ == "__main__":
    path = sys.argv[1]
    print(f">>> handle_arrival.py: main: path: {path}")

    arrival = SftpPlusArrivalHandler(path)
    print(f">>> arrival: {arrival}")
    arrival.named_file_name = "food"
    arrival.named_paths_name = "food"
    arrival.run_method = "collect_paths"
    arrival.process_arrival()
