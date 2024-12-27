from csvpath.managers.metadata import Metadata


class Dataset:
    def __init__(
        self, *, listener, manifest: dict[str, ...], metadata: Metadata
    ) -> None:
        self.listener = listener
        self.manifest = manifest
        self.metadata = metadata
        self._title = None
        self._name = None
        self._group = None
        self._visible = False
        self._org = None
        self._tags = None
        self._fields = None

    @property
    def fields(self) -> list[str]:
        return self._fields

    @fields.setter
    def fields(self, fs: list[str]) -> None:
        self._fields = fs

    @property
    def tags(self) -> list[str]:
        return self._tags

    @tags.setter
    def tags(self, ts: list[str]) -> None:
        self._tags = ts

    @property
    def name(self) -> str:
        if self._name is None:
            self._name = self.manifest.get("named_results_name")
            if self._name is None:
                self._name = self.manifest.get("named_paths_name")
        return self._name

    @name.setter
    def name(self, n: str) -> None:
        self._name = n

    @property
    def org(self) -> str:
        if self._org is None:
            #
            # not having self.metadata is only seen in testing atm.
            #
            if self.metadata:
                self._org = self.metadata.archive_name
            else:
                self._org = "csvpath"
        return self._org

    @org.setter
    def org(self, o: str) -> None:
        self._org = o

    @property
    def title(self) -> str:
        if self._title is None:
            self._title = self.manifest.get("named_paths_name")
            if self._title is None:
                self._title = self.manifest.get("named_results_name")
            if self._title is None:
                self._title = self.manifest.get("instance_name")
        return self._title

    @title.setter
    def title(self, t: str) -> None:
        self._title = t

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, v: bool) -> None:
        self._visible = v

    @property
    def author(self) -> str:
        return self.metadata.get("ckan-author")

    @property
    def author_email(self) -> str:
        return self.metadata.get("ckan-author_email")

    @property
    def url(self) -> str:
        return self.manifest.get("instance_home")

    @property
    def version(self) -> str:
        return self.manifest.get("uuid")

    @property
    def group(self) -> str:
        return self._group

    @group.setter
    def group(self, g: str) -> None:
        self._group = g

    @property
    def extras(self) -> list[dict[str, ...]]:
        #
        # this needs to be on the meta.json file, not the metadata event
        #
        extras = []
        for k, v in self.metadata.items():
            if k.endswith("-mode") or k.startswith("ckan-"):
                continue
            extras.append({k, v})
        return extras

    def groups(self) -> list[dict[str, ...]]:
        groups = []
        g = {}
        g["name"] = self.group
        groups.append(g)
        return groups
