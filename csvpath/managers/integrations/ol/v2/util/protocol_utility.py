from pathlib import Path

from csvpath.managers.metadata import Metadata
from csvpath.util.nos import Nos
from csvpath.util.config import Config
from csvpath.util.azure.azure_utils import AzureUtility as azut


class ProtocolUtility:
    @classmethod
    def update_protocol_if(cls, *, config: Config, mdata: Metadata, root: str) -> str:
        if root is None:
            raise ValueError("URI cannot be None")
        root = str(root).strip()
        if root == "":
            raise ValueError("URI cannot be empty")
        if config is None:
            raise ValueError("Config cannot be None")
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        #
        # look in config for openlineage.namespace
        #   - "" or default: nothing, use bare named-entity path
        #   - project: use bare prefixed by project_context/project, if available
        #   - name: use last path segment of named-entity path
        #   - strip: strip off the protocol, if any
        #
        # to test use config.set(section="listeners", name="openlineage.namespace", value=...)
        #
        ns = config.get(
            section="listeners", name="openlineage.namespace", default="default"
        )
        ret = cls._strip_if(root=root, ns=ns)
        ret = cls._name_if(root=ret, ns=ns)
        ret = cls._project_if(mdata=mdata, root=ret, ns=ns)
        ret = cls._default_if(root=ret, ns=ns)
        return ret

    @classmethod
    def _strip_if(cls, *, root: str, ns: str) -> str:
        if ns != "strip":
            return root
        root = cls._strip_protocol_if(root)
        return root

    @classmethod
    def _name_if(cls, *, root: str, ns: str) -> str:
        if ns != "name":
            return root
        _ = Path(root).name
        if _ == "":
            return f"csvpath://{root}"
        return f"csvpath://{_}"

    @classmethod
    def _project_if(cls, *, mdata: Metadata, root: str, ns: str) -> str:
        if ns != "project":
            return root
        _ = ""
        if mdata.project_context is not None:
            _ = mdata.project_context
        if mdata.project is not None:
            _ = f"{_}/{mdata.project}" if _ != "" else mdata.project
        ret = None
        if _ == "":
            ret = f"csvpath://{cls._strip_protocol_if(root)}"
        else:
            ret = f"csvpath://{cls._strip_protocol_if(_)}"
        if _ != "":
            last = Path(root).name
            ret = f"{ret}/{last}"
        return ret

    @classmethod
    def _default_if(cls, *, root: str, ns: str) -> str:
        if ns not in ["default", ""]:
            return root
        nos = Nos(root)
        if nos.is_local:
            if root.startswith("file://"):
                return root
            path = Path(root)
            try:
                return path.as_uri()
            except ValueError:
                return root
        elif nos.is_azure:
            p = azut.my_protocol()
            path = root[5:]
            return f"{p}{path}"
        return root

    @classmethod
    def _strip_protocol_if(cls, root: str) -> str:
        i = root.find("://")
        if i == -1:
            return root
        return root[i + 3 :]
