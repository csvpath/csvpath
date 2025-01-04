from ckanapi import RemoteCKAN
from ckanapi.errors import NotFound
from csvpath import CsvPaths
from csvpath.util.config import Config
from .dataset import Dataset
from .datafile import Datafile
import os


class CkanException(Exception):
    pass


class Ckan:
    def __init__(self, *, config, manifest, csvpaths=None) -> None:
        self.config = config
        self.csvpaths = csvpaths
        self._manifest = manifest
        self._client = None

    @property
    def manifest(self):
        return self._manifest

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        self._config = config

    @property
    def client(self):
        if self._client is None:
            server = self.config._get("ckan", "server")
            if server is None:
                raise CkanException(
                    "CKAN server cannot be None. Check config for [ckan] server"
                )
            token = self.config._get("ckan", "api_token")
            if token is None:
                raise CkanException(
                    "API token cannot be None. Check config for [ckan] api_token"
                )
            self._client = RemoteCKAN(server, apikey=token, user_agent="CsvPath")
        return self._client

    # ==========================
    # ==========================

    def create_or_update_dataset(self, dataset: Dataset) -> None:
        if self._has_dataset(dataset.name):
            self._update_dataset(dataset)
        else:
            self._create_dataset(dataset)

    def upload_datafile(self, datafile: Datafile) -> dict[str, ...]:
        with open(datafile.path, "rb") as file:
            id = self._has_resource(datafile.dataset_id, datafile.name)
            if id is not None:
                resource = self.client.action.resource_update(
                    id=id,
                    package_id=datafile.dataset_id,
                    url=datafile.url,
                    name=datafile.name,
                    mimetype=datafile.mime_type,
                    upload=file,
                )
            else:
                resource = self.client.action.resource_create(
                    package_id=datafile.dataset_id,
                    url=datafile.url,
                    name=datafile.name,
                    mimetype=datafile.mime_type,
                    upload=file,
                )
            return resource

    def create_group_if(self, *, name: str, title: str) -> None:
        #
        # the archive turns into a ckan group. orgs may run multiple CsvPaths.
        # and each named-group can be a dataset with multiple files.
        #
        thename = self._fix_name_if(name)
        if not self._has_group(thename):
            if title is not None and title != thename:
                self.client.action.group_create(name=thename, title=title)
            else:
                self.client.action.group_create(name=thename)
        return thename

    def _create_dataset(self, dataset: Dataset) -> None:
        if not self._has_org(dataset.org):
            raise CkanException(
                "You must provide the name of an organization. Ask your CKAN admin to create one for you."
            )
        args = {
            "name": self._fix_name_if(dataset.name),
            "title": dataset.title,
            "owner_org": dataset.org,
            "private": not dataset.visible,
            "url": dataset.url,
        }
        if dataset.tags is not None:
            args["tags"] = dataset.tags
        if dataset.fields is not None:
            args["extras"] = dataset.fields
        if dataset.groups is not None:
            args["groups"] = dataset.groups()
        #
        # author = dataset.author
        # author_email = dataset.author_email
        #
        # create dataset as a ckan package
        #
        self.client.action.package_create(**args)

    def _update_dataset(self, dataset: Dataset) -> None:
        args = {
            "id": self._fix_name_if(dataset.name),
            "title": dataset.title,
            "owner_org": dataset.org,
            "private": not dataset.visible,
            "url": dataset.url,
        }
        if dataset.tags is not None:
            args["tags"] = dataset.tags
        if dataset.fields is not None:
            args["extras"] = dataset.fields
        if dataset.groups is not None:
            args["groups"] = dataset.groups()
        #
        # version = dataset.version
        # author = dataset.author
        # author_email = dataset.author_email
        #
        self.client.action.package_patch(**args)

    # ==========================
    # ==========================

    def _fix_name_if(self, name: str) -> str:
        name = name.strip().lower()
        thename = ""
        for n in name:
            if n.isalnum() or n in ["-", "_"]:
                thename += n
            else:
                thename += "_"
        return thename

    def _has_org(self, name) -> bool:
        try:
            org = self.client.action.organization_show(id=name)
        except NotFound:
            #
            # not found is expected so we do nothing
            #
            ...
        return org is not None

    def _has_dataset(self, name) -> bool:
        dataset = None
        try:
            dataset = self.client.action.package_show(id=name)
        except NotFound:
            #
            # not found is expected so we do nothing
            #
            ...
        return dataset is not None

    def _has_group(self, name: str) -> bool:
        name = self._fix_name_if(name)
        groups = self.client.action.group_list(groups=[name])
        return groups and len(groups) == 1 and groups[0] == name

    def _has_resource(self, package_name, resource_name: str) -> str:
        dataset = None
        try:
            dataset = self.client.action.package_show(id=package_name)
            if "resources" in dataset:
                for r in dataset["resources"]:
                    if r.get("name") == resource_name:
                        return r["id"]
        except NotFound:
            #
            # not found is expected so we do nothing
            #
            ...
        return None
