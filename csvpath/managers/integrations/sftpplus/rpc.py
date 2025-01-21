import requests
from csvpath import CsvPaths
from csvpath.util.var_utility import VarUtility


class RpcException(Exception):
    ...


class Rpc:
    def __init__(self):
        self.csvpaths = CsvPaths()
        self._rpc_id = 0
        self._session_id = None
        self._url = None
        self._username = None
        self._password = None
        self._headers = {
            "content-type": "application/json;charset=utf-8",
            "user-agent": "/csvpath/",
        }
        self.start()

    def start(self) -> None:
        self._http = requests.Session()
        self._url = VarUtility.get(
            section="sftpplus",
            name="api_url",
            default="https://localhost:10020/json",
            config=self.csvpaths.config,
        )
        result = self.send("login", username=self.username, password=self.password)
        self._session_id = result["session_id"]

    @property
    def username(self) -> str:
        if self._username is None:
            self._username = VarUtility.get(
                section="sftpplus", name="admin_username", env="SFTPPLUS_ADMIN_USERNAME"
            )
        return self._username

    @property
    def password(self) -> str:
        if self._password is None:
            self._password = VarUtility.get(
                section="sftpplus", name="admin_password", env="SFTPPLUS_ADMIN_PASSWORD"
            )
        return self._password

    def send(self, command, **kwargs):
        self._rpc_id += 1
        data = {
            "jsonrpc": "2.0",
            "id": self._rpc_id,
            "method": command,
            "params": kwargs,
        }
        if self._session_id:
            data["session_id"] = self._session_id
        response = None
        results = None
        ret = None
        try:
            response = self._http.post(
                self._url,
                headers=self._headers,
                verify=False,
                json=data,
            )
        except requests.exceptions.RequestException as e:
            raise RpcException(str(e)) from e
        if response.status_code != 200:
            raise RpcException(
                "Unknown response: %s: %s", response.status_code, response.reason
            )
        try:
            results = response.json()
        except ValueError as e:
            raise RpcException("Invalid JSON response.") from e
        error = results.get("error", {})
        if error:
            error_id = error.get("code", None)
            if not error_id:
                error_id = error.get("id", "UnknownID")
            message = error.get("message", "No error details.")
            raise RpcException("%s: %s" % (error_id, message))
        try:
            if self._rpc_id in results:
                ret = results[self._rpc_id]["result"]
            else:
                ret = results["result"]
        except KeyError as e:
            raise RpcException('Invalid response: no "result" key') from e
        return ret
