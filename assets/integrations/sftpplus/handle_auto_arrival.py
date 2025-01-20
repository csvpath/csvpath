import sys
import json
import os
from csvpath import CsvPaths
from csvpath.managers.integrations.sftpplus.arrival_handler import (
    SftpPlusArrivalHandler,
)

if __name__ == "__main__":
    paths = CsvPaths()
    path = sys.argv[1]
    h = SftpPlusArrivalHandler(path)
    h.process_arrival()
