import threading
import paramiko
from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.results.results_registrar import ResultsRegistrar
from csvpath.managers.results.result import Result
from csvpath.managers.listener import Listener
from csvpath.util.box import Box
from csvpath.util.nos import Nos
from csvpath.util.var_utility import VarUtility
from csvpath.util.file_readers import DataFileReader


#
# this class is for sending results to an SFTP location. it also run on
# result updates, but for now we'll just do results updates and loop over
# all the results.
#
#   sftp metadata fields and values are like e.g.:
#      sftp-server: localhost
#      sftp-port: 22
#      sftp-user: LOCAL_SFTP_USER
#      sftp-password: LOCAL_SFTP_PASSWORD
#      sftp-target-path: my_data/
#      sftp-files: data.csv > data.csv, unmatched.csv > var|unmatched_filename, errors.json > errors.json
#      sftp-original-data: send
#
class SftpSender(Listener, threading.Thread):
    def __init__(self, *, config=None):
        super().__init__(config)
        self._server = None
        self._port = None
        self._user = None
        self._password = None
        self._target_path = None
        self._files = []
        self._send_original = False
        self.csvpaths = None
        self.result = None
        self.metadata = None
        self.results = None

    def _collect_fields(self) -> None:
        m = self.result.csvpath.metadata
        v = self.result.csvpath.variables
        self._server = VarUtility.get_str(m, v, "sftp-server")
        self._port = VarUtility.get_int(m, v, "sftp-port")
        self._user = VarUtility.get_str(m, v, "sftp-user")
        self._password = VarUtility.get_str(m, v, "sftp-password")
        self._target_path = VarUtility.get_str(m, v, "sftp-target-path")
        self._original = VarUtility.get_bool(m, v, "sftp-original-data")
        self._files = VarUtility.get_value_pairs(
            metadata=m, variables=v, key="sftp-files"
        )

    def run(self):
        #
        # csvpath adds its config, but under it's thread's name, so we
        # have to do it again here.
        #
        Box().add(Box.CSVPATHS_CONFIG, self.csvpaths.config)

        self.csvpaths.logger.info("Checking for requests to send result files by SFTP")
        self.results = self.csvpaths.results_manager.get_named_results(
            self.metadata.named_results_name
        )
        for result in self.results:
            self.result = result
            self._collect_fields()
            self._metadata_update()
        #
        # clear out this thread
        #
        self.csvpaths.wrap_up()

    def metadata_update(self, mdata: Metadata) -> None:
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        if not isinstance(mdata, ResultsMetadata):
            if self.csvpaths:
                self.csvpaths.logger.warning(
                    "SftpSender only listens for results events. Other event types are ignored."
                )
            return
        if mdata.status == ResultsRegistrar.COMPLETE:
            self.metadata = mdata
            self.start()

    def _metadata_update(self) -> None:
        if (
            self._files is None or len(self._files) == 0
        ) and self._send_original is not True:
            # no files to send and not sending the original data means we're done
            return
        files = [
            "data.csv",
            "unmatched.csv",
            "errors.json",
            "vars.json",
            "meta.json",
            "printouts.txt",
            "manifest.json",
        ]
        sep = Nos(self.metadata.run_home).sep
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                self._server,
                self._port,
                self._user,
                self._password,
                allow_agent=False,
                look_for_keys=False,
            )
            sftp = client.open_sftp()
            self.csvpaths.logger.info("Preparing to send %s files", len(self._files))
            try:
                sftp.stat(self._target_path)
            except FileNotFoundError:
                sftp.mkdir(self._target_path)
            for pair in self._files:
                file = pair[0]
                to = pair[1]
                if file not in files:
                    raise ValueError("File name {file} is not in {files}")
                if to is None:
                    raise ValueError("File name {file} has no destination")
                path = f"{self.metadata.run_home}{sep}{self.result.identity_or_index}{sep}{file}"
                remote_path = f"{self._target_path}/{to}"
                self.csvpaths.logger.info("Putting %s to %s", path, remote_path)
                #
                # need to use data reader and stream. if we're
                # sftping from s3 or something this is going to
                # be slow
                #
                # sftp.put(path, remote_path)
                try:
                    sftp.stat(self._target_path)
                except FileNotFoundError:
                    sftp.mkdir(self._target_path)
                with DataFileReader(path) as reader:
                    flo = reader.source
                    f = sftp.open(remote_path, "wb")
                    f.write(flo.read())
                    f.close()
            #
            # send the original file if we need to. this will always be the normative
            # original, w/o regard to source-mode or by_line chaining or to rewind.
            #
            if self._original is True:
                path = self.results[0].csvpath.scanner.filename
                if path is None:
                    raise ValueError("Filename of first result cannot be None")
                remote_file = path[path.rfind(sep) + 1 :]
                remote_path = f"{self._target_path}/{remote_file}"
                sftp.put(path, remote_path)

            sftp.close()
        finally:
            client.close()
