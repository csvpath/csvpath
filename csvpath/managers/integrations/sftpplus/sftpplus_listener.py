import os
import json
import threading
import paramiko
from tempfile import NamedTemporaryFile
from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_metadata import PathsMetadata
from csvpath.managers.listener import Listener
from csvpath.util.var_utility import VarUtility


#
# this class listens for paths events. when it gets one it generates
# a file of instructions and sends them to an SFTPPlus mailbox account.
# a transfer on the landing dir moves the instructions to a holding
# location for future reference: `user`/csvpath_messages/handled
#
# before the move happens a script runs to process the instructions.
# the instructions set up a transfer for the named-paths group's
# expected file arrivals.
#
# that transfer executes a script that loads the files as named-files and
# executes a run of the named-paths on the new named-file. it then moves
# the arrived file to a holding location for process debugging reference.
# the single-source authorative file is at this point in the named-files
# inputs directory, whereever that is configured.
#
class SftpPlusListener(Listener, threading.Thread):
    def __init__(self, *, config=None):
        super().__init__(config)
        self._server = None
        self._port = None
        self._user = None
        self._password = None
        self._target_path = "csvpath_messages"
        self._delete_on_success = True
        self._publish = False
        self._expected_file_name = None
        self._execute_before_script_name = None
        self.csvpaths = None
        self.result = None
        self.metadata = None
        self.results = None

    def _collect_fields(self) -> None:
        # directives stuff:
        self._publish = VarUtility.get_bool(self.result, "sftpplus-publish")
        self._expected_file_name = VarUtility.get_str(
            self.result, "sftpplus-named-file-name"
        )
        self._method = VarUtility.get_str(self.result, "sftpplus-run-method")
        # config.ini stuff:
        self._user = self.csvpath.config.get(section="sftpplus", name="admin_user")
        if self._user is None:
            raise ValueError("SFTPPlus Admin username cannot be None")
        if self._user.isupper():
            self._user = os.getenv(self._user)
        self._password = self.csvpath.config.get(
            section="sftpplus", name="admin_password"
        )
        if self._password is None:
            raise ValueError("SFTPPlus Admin password cannot be None")
        if self._password.isupper():
            self._password = os.getenv(self._password)
        self._server = self.csvpath.config.get(section="sftpplus", name="server")
        if self._server is None:
            raise ValueError("SFTPPlus server cannot be None")
        if self._server.isupper():
            self._server = os.getenv(self._server)
        self._port = self.csvpath.config.get(section="sftpplus", name="port")
        if self._port is None:
            raise ValueError("SFTPPlus port cannot be None")
        if self._port.isupper():
            self._port = os.getenv(self._port)
        self._delete_on_success = self.csvpath.config.get(
            section="sftpplus",
            name="sftpplus-delete-on-success",
            default=self._delete_on_success,
        )

    @property
    def run_method(self) -> str:
        if self._method is None or self._method not in [
            "collect_paths",
            "fast_forward_paths",
            "collect_by_line",
            "fast_forward_by_line",
        ]:
            self.csvpaths.logger.warning(
                "No acceptable sftpplus-run-method found by SftpSender for {self.metadata.named_paths_name}: {self._method}. Defaulting to collect_paths."
            )
            self._method = "collect_paths"
        return self._method

    @property
    def scripts_base(self) -> str:
        return self.csvpaths.config.get(section="sftppath", name="scripts_base")

    @property
    def script_dir(self) -> str:
        return self.csvpaths.config.get(section="sftppath", name="scripts_dir")

    @property
    def execute_before_script_name(self) -> str:
        return self.csvpaths.config.get(
            section="sftppath", name="execute_before_script_name"
        )

    def run(self):
        self.csvpaths.logger.info("Checking for requests to send result files by SFTP")
        self._metadata_update()

    def metadata_update(self, mdata: Metadata) -> None:
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        if not isinstance(mdata, PathsMetadata):
            if self.csvpaths:
                self.csvpaths.logger.warning(
                    "SftpplusListener only listens for paths events. Other event types are ignored."
                )
        self.metadata = mdata
        self.start()

    def _metadata_update(self) -> None:
        self._collect_fields()
        msg = self._create_instructions()
        self._send_message(msg)

    def _send_message(self, msg: dict) -> None:
        #
        # write instructions message into a temp file
        #
        with NamedTemporaryFile(mode="w+t", delete_on_close=False) as file:
            json.dump(msg, file, indent=2)
            file.close()
            file.seek(0)

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(self._server, self._port, self._user, self._password)
                sftp = client.open_sftp()
                self.csvpaths.logger.info(
                    "SFTPPlus listener prepping instruction to %s",
                    f"{self._user}/{self._target_path}",
                )
                #
                # create the remote dir, in the messages account, if needed.
                #
                try:
                    sftp.stat(self._target_path)
                except FileNotFoundError:
                    sftp.mkdir(self._target_path)
                #
                # land the file at the UUID so that if anything weird we'll only ever
                # interfere with ourselves.
                #
                remote_path = f"{self._target_path}/{self.metadata.uuid_string}.txt"
                self.csvpaths.logger.info("Putting %s to %s", file, remote_path)
                sftp.putfo(file, remote_path)
                sftp.close()
            finally:
                client.close()

    def _create_instructions(self) -> dict:
        #
        # SFTPPLUS TRANSFER SETUP STUFF
        # we are making the file-receiving transfer, not the message-receiving
        # transfer. this will be used by the message-receiving transfer to prep
        # the landing site for new files to be run against this named-paths.
        #
        msg = {}
        msg["name"] = self.metadata.named_paths_name
        msg["method"] = self.metadata.named_paths_name
        msg[
            "execute_before"
        ] = f"{self.scripts_base}/{self.scripts_dir}/{self.execute_before_script_name}"
        msg["delete_source_on_success"] = f"{self._delete_on_success}"
        msg["source_uuid"] = "DEFAULT-LOCAL-FILESYSTEM"
        msg["source_path"] = f"{self._expected_file_name}"
        msg["destination_uuid"] = "DEFAULT-LOCAL-FILESYSTEM"
        msg["destination_path"] = f"{self._expected_file_name}/handled"
        msg["description"] = f"{self.metadata.uuid_string}"
        msg["named_file_name"] = f"{self._expected_file_name}"
        msg["publish"] = f"{self._publish}"
