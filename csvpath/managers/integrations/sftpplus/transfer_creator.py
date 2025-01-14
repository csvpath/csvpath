import subprocess
import os
import json
from csvpath import CsvPaths
from csvpath.util.config import Config


#
# this class listens for messages via an sftpplus transfer. when
# it gets one it generates instructions for admin-shell to create
# a new transfer for a particular data partner's named files.
#
# we generate a script for the new transfer. that script executes
# a python class to load the files as named-files and execute a
# run of the originating named-paths on the new named-file.
#
# the named-file receiving transfer then moves the arrived file to
# a holding location for process debugging reference. the single-
# source authorative file is at this point in the named-files
# inputs directory, wherever that is configured.
#
class SftpPlusTransferCreator:
    SFTPPLUS_ADMIN_USERNAME = "SFTPPATH_ADMIN_USERNAME"
    SFTPPLUS_ADMIN_PASSWORD = "SFTPPATH_ADMIN_PASSWORD"

    def __init__(self):
        self.csvpaths = CsvPaths()
        self._path = None
        self._msg = None

    @property
    def message_path(self) -> str:
        return self._path

    @message_path.setter
    def message_path(self, p: str) -> None:
        transfers_base_dir = self.csvpaths.config.get(
            section="sftpplus", name="transfers_base_dir"
        )
        mailbox_user = self.csvpaths.config.get(section="sftpplus", name="mailbox_user")
        self._path = f"{transfers_base_dir}{os.sep}{mailbox_user}{os.sep}{p}"

    @property
    def admin_username(self) -> str:
        n = os.getenv(SftpPlusTransferCreator.SFTPPLUS_ADMIN_USERNAME)
        if n is not None:
            return n
        return self.config.get(section="sftpplus", name="admin_username")

    @property
    def admin_password(self) -> str:
        pw = os.getenv(SftpPlusTransferCreator.SFTPPLUS_ADMIN_PASSWORD)
        if pw is not None:
            return pw
        return self.config.get(section="sftpplus", name="admin_password")

    @property
    def config(self) -> Config:
        return self.csvpaths.config

    def process_message(self, msg_path) -> None:
        if msg_path is not None:
            self.message_path = msg_path
        if self.message_path is None:
            raise ValueError("Message path cannot be none")

        self.log(f"processing: path: {msg_path}")
        #
        # loads method as a single string
        #
        msg = self._get_message()
        self.log(f"processing: msg: {msg}")
        #
        # the named-path uuid is in the message's (and transfer's) description field
        # iterate the existing transfers looking for a description matching the named-paths
        # group's uuid
        #
        tuuid = self._find_existing_transfer(msg)
        self.log(f"processing: tuuid: {tuuid}")
        #
        # if tuuid exists we update the existing transfer
        # otherwise we create a new transfer.
        #
        if tuuid is None:
            tuuid = self._create_new_transfer(msg=msg)
            self.log(f"processing: new tuuid: {tuuid}")
        else:
            self._update_existing_transfer(tuuid=tuuid, msg=msg)
            self.log("processing: updated existing")
        #
        # generate the script that will load the named-file and run the named-paths when
        # a new file arrives at the transfer.
        #
        self._generate_and_place_scripts(msg)
        self.log("processing: done")

    #
    # ===================
    #
    def _get_message(self) -> dict:
        msg = None
        print(f"transcrt._get_msg: cwd: {os.getcwd()}, mp: {self.message_path}")
        with open(self.message_path, "r", encoding="utf-8") as file:
            msg = json.load(file)
        uuid = msg.get("uuid")
        if uuid is None:
            raise ValueError(
                f"uuid of named-paths group must be present in transfer setup message: {msg}"
            )
        #
        # any other validations here
        #
        self._msg = msg
        return msg

    def _cmd(self, cmd: str) -> str:
        admin_shell = self.csvpaths.config.get(section="sftpplus", name="admin_shell")
        c = f"""{admin_shell} -k -u {self.admin_username} -p - {cmd} """
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
            #
            # our uuid is in the description field. when we see it we know we
            # found the existing transfer, so we get the transfer's uuid.
            #
            if t.find(msg["uuid"]) > -1:
                i = t.find("uuid = ")
                tuuid = t[i + 9 : t.find('"', i + 10)]
        return tuuid

    def _create_new_transfer(self, *, msg: dict) -> str:
        # create the commands
        tuuid = self._create_transfer(msg["named_file_name"])
        execute = self._execute_before_script
        transfers_base_dir = self.csvpath.config.get(
            section="sftpplus", name="transfers_base_dir"
        )
        account_name = msg["account_name"]
        named_file_name = msg["named_file_name"]
        source = f"{transfers_base_dir}{os.sep}{account_name}{os.sep}{named_file_name}"
        destination = f"{source}{os.sep}handled"
        active = msg["active"].lower() if "active" in msg else "true"
        cmds = [
            self._cmd(f'configure transfer {tuuid} execute_before "{execute}"'),
            self._cmd(f'configure transfer {tuuid} source_path "{source}"'),
            self._cmd(f'configure transfer {tuuid} destination_path "{destination}"'),
            self._cmd(f"configure transfer {tuuid} enabled={active}"),
        ]
        for cmd in cmds:
            self._run_cmd(cmd)

    def _create_transfer(self, name: str) -> str:
        c = self._cmd(f"add transfer {name}")
        o = self._run_cmd(c)
        #
        # output is like:
        #   New transfers created with UUID: f6ec10a0-baff-449d-9ba2-f89748b10dd4
        #
        i = o.find("UUID: ")
        tuuid = o[i + 6 :]
        tuuid = tuuid.strip()
        print(f"_create_transfer: tuuid: {tuuid}")
        return tuuid

    def _run_cmd(self, cmd: str) -> str:
        parts = cmd.split(" ")
        parts = [s for s in parts if s.strip() != ""]
        print(f"running command: admin: {self.admin_password}")
        for p in parts:
            print(f"   {p}")
        result = subprocess.run(
            parts, input=f"{self.admin_password}\n", capture_output=True, text=True
        )
        code = result.returncode
        output = result.stdout
        error = result.stderr
        print(f"_run_command: code: {code}, error: {error}")
        print(f"_run_command: output: {output}")
        return output

    @property
    def _execute_before_script(self) -> str:
        #
        # we create one of these for every transfer
        #
        scripts = self.csvpath.config.get(section="sftpplus", name="scripts_dir")
        account_name = self._msg["account_name"]
        named_file_name = self._msg["named_file_name"]
        path = f"{scripts}{os.sep}{account_name}{os.sep}{named_file_name}{os.sep}handle_arrival.sh"
        print(f"_execute_before_script: path: {path}")
        return path

    def _execute_before_python_main(self) -> str:
        #
        # we just need one of these, total. if not found, we'll create it.
        #
        scripts = self.csvpath.config.get(section="sftpplus", name="scripts_dir")
        path = f"{scripts}{os.sep}arrival_handler_main.py"
        return path

    def _update_existing_transfer(self, *, tuuid: str, msg: dict) -> None:
        cmds = [
            #
            # we'll take execute_before to give us a relatively easy way to allow for
            # the script changing.
            #
            self._cmd(f"configure transfer {tuuid} enabled = {msg['active']}"),
        ]
        for cmd in cmds:
            self._run_cmd(cmd)

    @property
    def python_cmd(self) -> str:
        return f"{self.csvpaths.config.get(section='sftpplus', name='python_cmd')} "

    def _generate_and_place_scripts(self, msg: dict) -> str:
        before_script = self._execute_before_script
        print(f"transfer script path is: {before_script}")
        s = f"""
#
# THIS FILE IS GENERATED AT RUNTIME. DO NOT EDIT IT.
#
{self.python_cmd} {self._execute_before_python_main} "$1"
        """
        print(f"_generate_and_place_scripts: python runner script: {s}")
        with open(before_script, "w", encoding="utf-8") as file:
            file.write(s)
        #
        # do we need to +x the script?
        #
        #
        # create the main.py that uses the handler to add the new named-file
        # and run the named-paths group
        #
        if not os.path(self._execute_before_python_main).exists():
            method = msg["method"]
            named_paths_name = msg["named_paths_name"]
            account_name = msg["account_name"]
            s = f"""
import sys
import os
from csvpath import CsvPaths
from csvpath.managers.integrations.sftpplus.arrival_handler import SftpPlusArrivalHandler
#
# THIS FILE IS GENERATED AT RUNTIME. DO NOT EDIT IT.
# args:
#  - account_name (account name)
#  - named file name
#  - arriving filename
#
if __name__ == "__main__":
    paths = CsvPaths()
    account_name = {account_name}
    named_file_name = {named_file_name}
    file_name = arg[1]
    transfers_base = paths.config.get(section="sftpplus", name="transfers_base_dir")
    path = f"{{transfers_base}}{{os.sep}}{{account_name}}{{os.sep}}{{named_file_name}}{{os.sep}}{{file_name}}" # noqa: F821
    h = SftpPlusArrivalHandler(path)
    # create the path here
    h.named_file_name = named_file_name
    h.run_method = "{method}"
    h.named_paths_name = "{named_paths_name}"
    h.process_arrival()
"""
            with open(self._execute_before_python_main, "w", encoding="utf-8") as file:
                file.write(s)
