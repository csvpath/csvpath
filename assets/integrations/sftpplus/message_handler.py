import sys
from csvpath.managers.integrations.sftpplus.transfer_creator import (
    SftpPlusTransferCreator,
)

if __name__ == "__main__":
    message = sys.args[1]
    SftpPlusTransferCreator().process_message(message)
