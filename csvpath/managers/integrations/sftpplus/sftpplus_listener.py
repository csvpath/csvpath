import os
import json
import threading
import paramiko
from tempfile import NamedTemporaryFile
from csvpath import CsvPaths
from csvpath.util.box import Box
from csvpath.managers.metadata import Metadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.listener import Listener
from csvpath.util.var_utility import VarUtility
from csvpath.util.metadata_parser import MetadataParser


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
        self._mailbox_user = None
        self._mailbox_password = None
        self._active = False
        self._named_file_name = None
        self._account_name = None
        self._run_method = None
        self._execute_timeout = None
        self.csvpaths = CsvPaths()
        self.result = None
        self.metadata = None
        self.results = None

    def _collect_fields(self) -> None:
        # collect the metadata from comments. we don't have vars so just an
        # empty set there. as we loop through we will overwrite metadata keys
        # if there are dups across the csvpaths. this raises the topic of
        # how to organize data providers/streams in CsvPath. regardless, there
        # are enough ways to organize that imho we don't have to be overly
        # sensitive to the constraint here.
        m = {}
        for p in self.metadata.named_paths:
            MetadataParser(None).collect_metadata(m, p)
        v = {}
        # comments metadata
        self._active = VarUtility.get_bool(m, v, "sftpplus-active")
        self._account_name = VarUtility.get_str(m, v, "sftpplus-account-name")
        self._named_file_name = VarUtility.get_str(m, v, "sftpplus-named-file-name")
        self._run_method = VarUtility.get_str(m, v, "sftpplus-run-method")
        self._execute_timeout = VarUtility.get_int(m, v, "sftpplus-execute-timeout")
        #
        # config.ini stuff:
        #
        # user
        #
        self._mailbox_user = VarUtility.get(
            section="sftpplus",
            name="mailbox_user",
            default="mailbox",
            config=self.csvpaths.config,
        )
        #
        # password
        #
        self._mailbox_password = VarUtility.get(
            section="sftpplus", name="mailbox_password", config=self.csvpaths.config
        )
        #
        # server
        #
        self._server = VarUtility.get(
            section="sftpplus",
            name="server",
            default="localhost",
            config=self.csvpaths.config,
        )
        #
        # port
        #
        self._port = VarUtility.get(
            section="sftpplus", name="port", default=10022, config=self.csvpaths.config
        )

    @property
    def run_method(self) -> str:
        if self._run_method is None or self._method not in [
            "collect_paths",
            "fast_forward_paths",
            "collect_by_line",
            "fast_forward_by_line",
        ]:
            self.csvpaths.logger.warning(
                "No acceptable sftpplus-run-method found by SftpSender for {self.metadata.named_paths_name}: {self._method}. Defaulting to collect_paths."
            )
            self._run_method = "collect_paths"
        return self._run_method

    def run(self):
        #
        # csvpath adds its config, but under it's thread's name, so we
        # have to do it again here.
        #
        Box().add(Box.CSVPATHS_CONFIG, self.csvpaths.config)
        self.csvpaths.logger.info("Checking for requests to send result files by SFTP")
        self._metadata_update()
        self.csvpaths.wrap_up()

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
        if not self._has_fields_needed():
            self.csvpaths.logger.info(
                "SftpPlus listener does not have the fields needed to create a transfer for this named-paths"
            )
            return
        msg = self._create_instructions()
        self._send_message(msg)

    def _has_fields_needed(self) -> bool:
        self.csvpaths.logger.debug("SftpPlus listener fields: server: %s", self._server)
        self.csvpaths.logger.debug("SftpPlus listener fields: port: %s", self._port)
        self.csvpaths.logger.debug(
            "SftpPlus listener fields: mailbox_user: %s", self._mailbox_user
        )
        self.csvpaths.logger.debug(
            "SftpPlus listener fields: mailbox_password: %s", self._mailbox_password
        )
        self.csvpaths.logger.debug(
            "SftpPlus listener fields: named_file_name: %s", self._named_file_name
        )
        self.csvpaths.logger.debug(
            "SftpPlus listener fields: account_name: %s", self._account_name
        )
        self.csvpaths.logger.debug(
            "SftpPlus listener fields: run_method: %s", self._run_method
        )
        if self._server is None:
            return False
        if self._port is None:
            return False
        if self._mailbox_user is None:
            return False
        if self._mailbox_password is None:
            return False
        if self._named_file_name is None:
            return False
        if self._account_name is None:
            return False
        if self._run_method is None:
            return False
        return True

    def _send_message(self, msg: dict) -> None:
        #
        # write instructions message into a temp file
        #
        with NamedTemporaryFile(mode="w+t") as file:
            json.dump(msg, file, indent=2)
            file.seek(0)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(
                    self._server, self._port, self._mailbox_user, self._mailbox_password
                )
                #
                # create the remote dir, in the messages account, if needed.
                #
                sftp = client.open_sftp()
                #
                # land the file at the UUID so that if anything weird we'll only ever
                # interfere with ourselves.
                #
                remote_path = f"{self._account_name}-{msg['named_file_name']}-{msg['named_paths_name']}.json"
                self.csvpaths.logger.info("Putting %s to %s", file, remote_path)
                sftp.putfo(file, remote_path)
                sftp.close()
            finally:
                client.close()

    def _create_instructions(self) -> dict:
        #
        # SFTPPLUS TRANSFER SETUP STUFF
        # we are collecting info for the transfer creator class.
        # it will be used to create the message-receiving transfer
        # that handles new file arrivals.
        #
        # most of the information the transer creating code needs comes
        # from its own config.ini.
        #
        msg = {}
        msg["named_paths_name"] = self.metadata.named_paths_name
        msg["account_name"] = self._account_name
        msg["method"] = self._run_method
        #
        # make "description" to "uuid". doesn't matter here
        # that it ends up in the transfer's description field
        #
        msg["uuid"] = f"{self.metadata.uuid_string}"
        msg["named_file_name"] = f"{self._named_file_name}"
        msg["active"] = self._active
        if self._execute_timeout is None:
            self._execute_timeout = 300
        msg["execute_timeout"] = self._execute_timeout
        return msg
