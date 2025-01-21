from .rpc import Rpc


class Transfers:
    def __init__(self):
        self._rpc = None

    @property
    def rpc(self) -> Rpc:
        if self._rpc is None:
            self._rpc = Rpc()
        return self._rpc

    @rpc.setter
    def rpc(self, rpc: Rpc) -> None:
        self._rpc = rpc

    def has_transfer(self, name) -> bool:
        return self.transfer_uuid_for_name(name) is not None

    def transfer_uuid_for_name(self, name) -> str:
        if not name:
            raise ValueError("Name cannot be None")
        result = self.rpc.send("get_index")
        transfers = result["configuration"]["transfers"]
        for k, v in transfers.items():
            if v.get("name") == name:
                return k
        return None

    def create_transfer(self, name, values: dict) -> None:
        values["name"] = name
        path = "transfers/"
        changes = {"0": {"operation": "create", "path": path, "value": values}}
        self.rpc.send(command="apply", changes=changes)

    def delete_transfer(self, uuid=None) -> None:
        if not uuid:
            raise ValueError("Uuid cannot be None")
        path = f"transfers/{uuid}"
        changes = {"0": {"operation": "delete", "path": path, "value": ""}}
        self.rpc.send(command="apply", changes=changes)

    def update_transfer(
        self, *, name=None, uuid=None, update: str, value: str | int | bool
    ) -> None:
        if not name and not uuid:
            raise ValueError("Name and uuid cannot both be None")
        if name is None:
            name = uuid
        path = f"transfers/{name}/{update}"
        changes = {"0": {"operation": "update", "path": path, "value": value}}
        self.rpc.send(command="apply", changes=changes)
