import subprocess
import os
import json
from csvpath import CsvPaths
from csvpath.util.config import Config


#
# this class listens for messages. when it gets one it generates
# instructions for admin-shell.
#
# we also generate another script for the new transfer. that script
# loads the files as named-files and executes a run of the named-paths
# on the new named-file.
#
# it then moves the arrived file to a holding location for process
# debugging reference. the single-source authorative file is at this
# point in the named-files inputs directory, whereever that is
# configured.
#
class SftpPlusTransferCreator:
    CSVPATH_ADMIN_PASSWORD = "CSVPATH_ADMIN_PASSWORD"

    def __init__(self):
        self._csvpaths = CsvPaths()
        self._path = None

    @property
    def message_path(self) -> str:
        return self._path

    @message_path.setter
    def message_path(self, p: str) -> None:
        self._path = p

    @property
    def admin_username(self) -> str:
        n = os.getenv(SftpPlusTransferCreator.CSVPATH_ADMIN_PASSWORD)
        if n is not None:
            return n
        return self.config["sftpplus"]["admin_username"]

    @property
    def admin_password(self) -> str:
        pw = os.getenv(SftpPlusTransferCreator.CSVPATH_ADMIN_PASSWORD)
        if pw is not None:
            return pw
        return self.config["sftpplus"]["admin_password"]

    @property
    def config(self) -> Config:
        return self._csvpaths.config

    def process_message(self, msg_path) -> None:
        #
        # loads method as a single string
        #
        msg = self._get_message()
        #
        # the named-path uuid is in the message's (and transfer's) description field
        # iterate the existing transfers looking for a description matching the named-paths
        # group's uuid
        #
        tuuid = self._find_existing_transfer(msg)
        #
        # if tuuid exists we update the existing transfer
        # otherwise we create a new transfer.
        #
        if tuuid is None:
            tuuid = self._create_new_transfer(msg=msg)
        else:
            self._update_existing_transfer(tuuid=tuuid, msg=msg)
        #
        # generate the script that will load the named-file and run the named-paths when
        # a new file arrives at the transfer.
        #
        self._generate_and_place_scripts(msg)

    #
    # ===================
    #
    def _get_message(self) -> dict:
        msg = None
        with open(self.message_path, "r", encoding="utf-8") as file:
            msg = json.load(file)
        uuid = msg.get("uuid")
        if uuid is None:
            raise ValueError(
                "uuid of named-paths group must be present in transfer setup message: {msg}"
            )
        #
        # any other validations here
        #
        return msg

    def _cmd(self, cmd: str) -> str:
        c = """echo {self.admin_password} | ./bin/admin-shell.sh -k -u {self.admin_username} -p - {cmd} """
        return c

    def _find_existing_transfer(self, msg: dict) -> str:
        #
        # we use admin-shell's show transfer command to find our uuid match in
        # the description field. if we find that we return the transfer's uuid.
        # if the transfer exists we want to update it.
        #
        # create the command:
        cmd = self._cmd("show transfer")
        # run the command
        out = self._run_cmd(cmd)
        # parse the list
        tuuid = None
        ts = out.split("--------------------------------------------------")
        for t in ts:
            if t.find(msg["uuid"]) > -1:
                i = t.find("uuid = ")
                tuuid = t[i + 8 : t.find('"', start=i + 9)]
        return tuuid

    def _run_cmd(self, cmd: str) -> str:
        parts = cmd.split(" ")
        result = subprocess.run(parts, capture_output=True, text=True)
        code = result.returncode
        output = result.stdout
        error = result.stderr
        print(f"_run_command: code: {code}, error: {error}")
        print(f"_run_command: output: {output}")
        return output

    def _create_transfer(self, name: str) -> str:
        c = self._cmd(f"add transfer {name}")
        o = self._run_cmd(c)
        #
        # output is like:
        #   New transfers created with UUID: f6ec10a0-baff-449d-9ba2-f89748b10dd4
        #
        i = o.find("UUID: ")
        tuuid = o[i + 1 :]
        print(f"_create_transfer: output: {o}")
        print(f"_create_transfer: tuuid: {tuuid}")
        return tuuid

    def _create_new_transfer(self, *, msg: dict) -> str:
        # create the commands
        tuuid = self._create_transfer(msg["named_file_name"])
        cmds = [
            self._cmd(
                f"configure transfer {tuuid} execute_before = {msg['execute_before']}"
            ),
            self._cmd(
                f"configure transfer {tuuid} delete_source_on_success = {msg['delete_source_on_success']}"
            ),
            self._cmd(f"configure transfer {tuuid} source_uuid = {msg['source_uuid']}"),
            self._cmd(f"configure transfer {tuuid} source_path = {msg['source_path']}"),
            self._cmd(
                f"configure transfer {tuuid} destination_uuid = {msg['destination_uuid']}"
            ),
            self._cmd(
                f"configure transfer {tuuid} destination_path = {msg['destination_path']}"
            ),
            self._cmd(f"configure transfer {tuuid} enabled = {msg['publish']}"),
        ]
        for cmd in cmds:
            self._run_cmd(cmd)

    def _update_existing_transfer(self, *, tuuid: str, msg: dict) -> None:
        cmds = [
            #
            # we'll take execute_before to give us a relatively easy way to allow for
            # the script changing.
            #
            self._cmd(
                f"configure transfer {tuuid} execute_before = {msg['execute_before']}"
            ),
            self._cmd(
                f"configure transfer {tuuid} delete_source_on_success = {msg['delete_source_on_success']}"
            ),
            self._cmd(f"configure transfer {tuuid} enabled = {msg['publish']}"),
        ]
        for cmd in cmds:
            self._run_cmd(cmd)

    def _generate_and_place_scripts(self, msg: dict) -> str:
        path = msg["execute_before"]
        #
        # we may need a setting for using poetry vs. pip, etc.
        #
        s = """
poetry run python transfer_creator_main.py "$1"
        """
        with open(path, "w", encoding="utf-8") as file:
            file.write(s)
        #
        # do we need to +x the script?
        #
        #
        # create the main.py that uses the handler to add the new named-file
        # and run the named-paths group
        #
        s = """
import sys
from csvpath.managers.integrations.sftpplus.arrival_handler import SftpPlusArrivalHandler

if __name__ == "__main__":
    path = sys.argv[1]
    h = SftpPlusArrivalHandler(path)
    h.named_file_name = "{msg['named_file_name']}"
    h.run_method = "{msg['method']}"
    h.named_paths_name = "{msg['name']}"
    h.process_arrival()
"""
        with open(path, "w", encoding="utf-8") as file:
            file.write(s)
