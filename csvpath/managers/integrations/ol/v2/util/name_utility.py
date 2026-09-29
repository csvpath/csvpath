from csvpath.util.references.reference_parser import ReferenceParser


class NameUtility:
    @classmethod
    def from_root_major_if(cls, name: str) -> str:
        if name is None:
            return None
        name = name.strip()
        if name[0] == "$":
            name = ReferenceParser(name).root_major
        return name

    @classmethod
    def trim_namespace_if(cls, *, namespace: str, path: str) -> str:
        if path.startswith(namespace):
            path = path[len(namespace) + 1 :]
            return path
        elif path.find(namespace) > -1:
            home = path[path.find(namespace) + len(namespace) + 1 :]
            return home
        return path
