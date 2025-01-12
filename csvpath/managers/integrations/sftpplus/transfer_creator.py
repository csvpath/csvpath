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
    SFTPPLUS_ADMIN_USERNAME = "SFTPPATH_ADMIN_USERNAME"
    SFTPPLUS_ADMIN_PASSWORD = "SFTPPATH_ADMIN_PASSWORD"

    def __init__(self):
        self._csvpaths = CsvPaths()
        self._path = None
        self._msg = None

    @property
    def message_path(self) -> str:
        return self._path

    @message_path.setter
    def message_path(self, p: str) -> None:
        #
        # f"{mailbox_path}/{mailbox_user}/{mailbox_name}/{p}"
        #
        self._path = f"/srv/storage/test_user/mailbox/{p}"

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
        return self._csvpaths.config

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
        uuid = msg.get("description")
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
        c = f"""/opt/sftpplus/bin/admin-shell.sh -k -u {self.admin_username} -p - {cmd} """
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
            if t.find(msg["description"]) > -1:
                i = t.find("uuid = ")
                tuuid = t[i + 9 : t.find('"', i + 10)]
                print(f"found tuuid: {tuuid}")
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

    @property
    def _execute_before_script(self) -> str:
        path = f"/opt/sftpplus/run/csvpath_sftpplus/{self._msg['named_file_name']}/handle_arrival.sh"
        print(f"_execute_before_script: path: {path}")
        return path

    def _execute_before_python_main(self) -> str:
        path = "/opt/sftpplus/run/csvpath_sftpplus/arrival_handler_main.py"
        return path

    def _create_new_transfer(self, *, msg: dict) -> str:
        # create the commands
        tuuid = self._create_transfer(msg["named_file_name"])
        execute = self._execute_before_script
        # execute = f"/opt/sftpplus/run/csvpath_sftpplus/{msg['named_file_name']}/handle_arrival.sh"
        source = f"/srv/storage/{msg['named_file_name']}"
        dest = f"{source}/handled"
        cmds = [
            self._cmd(f'configure transfer {tuuid} execute_before "{execute}"'),
            # self._cmd(f"configure transfer {tuuid} delete_source_on_success = true "),
            self._cmd(f'configure transfer {tuuid} source_path "{source}"'),
            self._cmd(f'configure transfer {tuuid} destination_path "{dest}"'),
            # self._cmd(f'configure transfer {tuuid} enabled=true'),
        ]
        for cmd in cmds:
            self._run_cmd(cmd)

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
        return "/root/.local/bin/poetry run python "

    def _generate_and_place_scripts(self, msg: dict) -> str:
        path = self._execute_before_script
        print(f"transfer script path is: {path}")
        s = f"""
#
# THIS FILE IS GENERATED AT RUNTIME. DO NOT EDIT IT.
#
# add named_file_name, filename here (and named_paths_name?)
{self._python_cmd} run python arrival_handler_main.py "$1"
        """
        print(f"_generate_and_place_scripts: python runner script: {s}")
        with open(path, "w", encoding="utf-8") as file:
            file.write(s)
        #
        # do we need to +x the script?
        #
        #
        # create the main.py that uses the handler to add the new named-file
        # and run the named-paths group
        #
        if not os.path(self._execute_before_python_main).exists():
            s = f"""
import sys
import os
from csvpath import CsvPaths
from csvpath.managers.integrations.sftpplus.arrival_handler import SftpPlusArrivalHandler
#
# THIS FILE IS GENERATED AT RUNTIME. DO NOT EDIT IT.
#
if __name__ == "__main__":
    paths = CsvPaths()
    named_file_name = sys.argv[1]
    file_name = sys.argv[2]
    transfers_base = paths.config.get(section="sftpplus", name="transfers_base_dir")
    path = f"{transfers_base}{os.sep}{named_file_name}{os.sep}{file_name}" # noqa: F821
    h = SftpPlusArrivalHandler(path)
    # create the path here
    h.named_file_name = named_file_name
    h.run_method = "{msg['method']}"
    h.named_paths_name = "{msg['named_paths_name']}"
    h.process_arrival()
"""
            with open(path, "w", encoding="utf-8") as file:
                file.write(s)
