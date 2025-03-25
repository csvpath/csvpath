import subprocess
import os
import shutil
import json
from csvpath import CsvPaths
from csvpath.util.config import Config
from csvpath.util.var_utility import VarUtility
from .transfers import Transfers

#
# this class listens for messages via an sftpplus transfer.
#
# it creates a new transfer to handle a data partner's named files.
# transfer name is: <<account>>-<<named-file>>-<<named-paths>>.
# where account == the SFTPPlus account == the data partner's name.
#
# if such a transfer already exists this class updates it or
# deletes it. a delete happens when the active key == "delete",
# rather than yes/true or no/false. beside active, the only other
# updateable field is the transfer's description. the description
# is always the latest uuid of the named-paths group that is
# modifying the transfer.
#
# once the transfer is created this class copies the metadata message
# file into the meta dir: /<<account>>/<<named-file>>/meta. this is
# the location the transfer will look for instructions for handling
# files. there will be one meta/<<uuid>>.json for every named-paths
# group that has an interest in the named-file.
#
# when this ^^^^ is done the mailbox transfer moves the message
# file to mailbox/handled.
#


class SftpPlusTransferCreator:

    SFTPPLUS_ADMIN_USERNAME = "SFTPPATH_ADMIN_USERNAME"
    SFTPPLUS_ADMIN_PASSWORD = "SFTPPATH_ADMIN_PASSWORD"
    HANDLE_AUTO_ARRIVAL = "handle_auto_arrival"

    def __init__(self, path=None):
        self.csvpaths = CsvPaths()
        self._path = path
        self._msg = None
        self._admin_user = None
        self._admin_password = None

    @property
    def message_path(self) -> str:
        return self._path

    @message_path.setter
    def message_path(self, p: str) -> None:
        self._path = p

    @property
    def admin_username(self) -> str:
        if self._admin_user is None:
            VarUtility.get(
                section="sftpplus",
                name="admin_username",
                env=SftpPlusTransferCreator.SFTPPLUS_ADMIN_USERNAME,
                config=self.config,
            )
        return self._admin_user

    @property
    def admin_password(self) -> str:
        if self._admin_password is None:
            VarUtility.get(
                section="sftpplus",
                name="admin_password",
                env=SftpPlusTransferCreator.SFTPPLUS_ADMIN_PASSWORD,
                config=self.config,
            )
        return self._admin_password

    @property
    def config(self) -> Config:
        return self.csvpaths.config

    @property
    def _get_transfer_uuid(self) -> bool:
        return Transfers().transfer_uuid_for_name(self._transfer_name)

    @property
    def _transfer_name(self) -> str:
        msg = self.message
        name = (
            f"{msg['account_name']}-{msg['named_file_name']}-{msg['named_paths_name']}"
        )
        return name

    @property
    def _execute_before_script(self) -> str:
        scripts = self.csvpaths.config.get(section="sftpplus", name="scripts_dir")
        if os.name == "nt":
            path = f"{scripts}{os.sep}{SftpPlusTransferCreator.HANDLE_AUTO_ARRIVAL}.bat"
        else:
            path = f"{scripts}{os.sep}{SftpPlusTransferCreator.HANDLE_AUTO_ARRIVAL}.sh"
        return path

    @property
    def _paths(self) -> dict:
        msg = self.message
        base = self.message_path[0 : self.message_path.rfind(os.sep)]
        base = base[0 : base.rfind(os.sep)]
        account_name = msg["account_name"]
        named_file_name = msg["named_file_name"]
        account_dir = os.path.join(base, account_name)
        nfn = os.path.join(account_dir, named_file_name)
        handled = os.path.join(nfn, "handled")
        meta = os.path.join(nfn, "meta")
        paths = {
            "meta": meta,
            "handled": handled,
            "named-file": nfn,
            "account": account_dir,
        }
        self.csvpaths.logger.debug("created paths dict: %s", paths)
        return paths

    @property
    def message(self) -> dict:
        if self._msg is None:
            msg = None
            with open(self.message_path, "r", encoding="utf-8") as file:
                msg = json.load(file)
            if "account_name" not in msg:
                raise ValueError(
                    f"Account name must be present in transfer setup message: {msg}"
                )
            if "uuid" not in msg:
                raise ValueError(
                    f"Named-paths UUID must be present in transfer setup message: {msg}"
                )
            if "named_file_name" not in msg:
                raise ValueError(
                    f"Named-file-name must be present in transfer setup message: {msg}"
                )
            if "named_paths_name" not in msg:
                raise ValueError(
                    f"Named-paths-name must be present in transfer setup message: {msg}"
                )
            if "method" not in msg:
                raise ValueError(
                    f"Method must be present in transfer setup message: {msg}"
                )
            if "execute_timeout" not in msg:
                eto = self.csvpath.config.get(
                    section="sftpplus", name="execute_timeout", default=300
                )
                msg["execute_timeout"] = eto
            self._msg = msg
        return self._msg

    # ====================

    def process_message(self) -> None:
        if self.message_path is None:
            raise ValueError("Message path cannot be none")
        msg = self.message
        """
        print("\n******************************************************")
        print(f"TransferCreator.process_msg: processing: path: {self.message_path}")
        print(f"TransferCreator.process_msg: processing: msg: {msg}")
        print("******************************************************\n")
        """
        self.csvpaths.logger.debug(
            "Transfer creator processing %s: %s", self.message_path, msg
        )
        #
        # if tuuid exists we update the existing transfer
        # otherwise we create a new transfer.
        #
        uuid = self._get_transfer_uuid
        if uuid is None:
            self._create_new_transfer()
        else:
            self._update_existing_transfer(uuid)

    def _create_new_transfer(self) -> str:
        self.csvpaths.logger.debug("Creating a new transfer")
        msg = self.message
        #
        # make the dirs the transfer needs. the account dir must already exist
        #
        paths = self._paths
        nfn = paths["named-file"]
        if not os.path.exists(nfn):
            os.mkdir(nfn)
            self.csvpaths.logger.debug(
                f"_create_new_transfer: created named file dir: {nfn}"
            )
        else:
            self.csvpaths.logger.debug(
                f"_create_new_transfer: named file dir already exists: {nfn}"
            )

        handled = paths["handled"]
        if not os.path.exists(handled):
            os.mkdir(handled)
            self.csvpaths.logger.debug(
                f"_create_new_transfer: created handled dir: {handled}"
            )
        else:
            self.csvpaths.logger.debug(
                f"_create_new_transfer: handled dir already exists: {handled}"
            )

        meta = paths["meta"]
        if not os.path.exists(meta):
            os.mkdir(meta)
            self.csvpaths.logger.debug(
                f"_create_new_transfer: created meta dir: {meta}"
            )
        else:
            self.csvpaths.logger.debug(f"_create_new_transfer: meta dir exists: {meta}")

        msg["source"] = paths["named-file"]
        msg["destination"] = paths["handled"]
        #
        # copy the message file to the meta dir for the transfer script to use
        #
        mfn = self.message_path
        self.csvpaths.logger.debug(
            "_create_new_transfer: message_path is %s", self.message_path
        )
        if mfn.find(os.sep) > -1:
            i = mfn.rfind(os.sep)
            mfn = mfn[i + 1 :]
        mfnp = os.path.join(paths["meta"], mfn)
        self.csvpaths.logger.debug(
            "_create_new_transfer: copying meta file to %s", mfnp
        )
        shutil.copy(self.message_path, mfnp)
        #
        # create sftpplus transfer
        #
        ts = Transfers()
        values = {
            "name": self._transfer_name,
            "execute_before": self._execute_before_script,
            "enabled": VarUtility.is_true(msg["active"]),
            "source_path": msg["source"],
            "destination_path": msg["destination"],
            "description": msg["uuid"],
            "execute_timeout": msg["execute_timeout"],
            "delete_source_on_success": True,
            "recursive": False,
            "overwrite_rule": "overwrite",
        }
        ts.create_transfer(values["name"], values)

    def _update_existing_transfer(self, tuuid: str) -> None:
        self.csvpaths.logger.debug(f"Updating an existing transfer: tuuid: {tuuid}")
        msg = self.message
        ts = Transfers()
        active = msg.get("active")
        if active == "delete":
            ts.delete_transfer(uuid=tuuid)
        else:
            ts.update_transfer(
                uuid=tuuid, update="enabled", value=VarUtility.is_true(msg["active"])
            )
            ts.update_transfer(uuid=tuuid, update="description", value=msg["uuid"])
            paths = self._paths
            shutil.copy(self.message_path, paths["meta"])
