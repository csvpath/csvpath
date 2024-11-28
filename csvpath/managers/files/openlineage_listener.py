import os
import json
import logging
import requests
from csvpath.util.exceptions import InputException
import http.client as http_client


class OpenLineageListener:
    def __init__(self, config):
        self.config = config

    def create_namespace(self) -> dict:
        http_client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

        n = {"ownerName": "David", "description": "wow"}
        # n["ownerName"] = "David",
        # n["description"] = "Wow"
        headers = {"Content-Type": "application/json"}
        r = requests.put(
            "http://localhost:5000/api/v1/namespaces/first", json=n, headers=headers
        )
        print(r)
        print(r.json())

    def metadata_update(self, mdata) -> None:
        n = {}
        p = "https://github.com/csvpath"
        #  mdata.time.strftime("%Y-%m-%dT%H:%M:%S%z")
        n["eventTime"] = "2024-12-28T19:52:00.001+10:00"
        n["producer"] = p
        n["schemaURL"] = "https://openlineage.io/spec/0-0-1/OpenLineage.json"
        ds = {}
        n["dataset"] = ds
        ds["namespace"] = mdata.named_file_name
        ds["name"] = mdata.file_name
        fs = {}
        ds["facets"] = fs

        bf = "https://openlineage.io/spec/1-0-2/OpenLineage.json#/$defs/BaseFacet"
        f = {}
        fs["uuid"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = f"{mdata.uuid}"

        f = {}
        fs["origin"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata.origin_path

        f = {}
        fs["archive_path"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata.archive_path

        f = {}
        fs["name_home"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata.name_home

        f = {}
        fs["file_home"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata.file_home

        f = {}
        fs["fingerprint"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata.fingerprint

        f = {}
        fs["mark"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata.mark

        f = {}
        fs["type"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata.type

        f = {}
        fs["manifest_path"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata.manifest_path

        t = json.dumps(n, indent=2)
        # print(f"json is: \n{t}")
        """
        with open(manifest_path, "w", encoding="utf-8") as file:
            json.dump(jdata, file, indent=2)
        """
        return t


if __name__ == "__main__":
    ol = OpenLineageListener(None)
    from csvpath.managers.files.file_metadata import FileMetadata

    m = FileMetadata()
    m.named_file_name = "fish"
    m.origin_path = "m/n/o"
    m.archive_path = "a/b/c"
    m.name_home = "z/y/x"
    m.file_home = "e/f/g"
    m.file_name = "fish.csv"
    m.fingerprint = "1234"
    m.mark = None
    m.type = "csv"
    m.manifest_path = "d/e/f"
    p = ol.metadata_update(m)

    """
    params = {
        "eventType": "START",
        "eventTime": "2020-12-28T19:52:00.001+10:00",
        "run": {
          "runId": "0176a8c2-fe01-7439-87e6-56a1a1b4029f"
        },
        "job": {
          "namespace": "my-namespace",
          "name": "my-job"
        },
        "inputs": [{
          "namespace": "my-namespace",
          "name": "my-input"
        }],
        "producer": "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client",
        "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent"
      }
    """
    headers = {"Content-Type": "application/json"}

    #
    # =================
    #
    """
    import requests
    import logging
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    """

    """
    r = requests.post(
        'http://localhost:5000/api/v1/lineage',
        json=p,
        headers=headers
    )
    print(r)
    print(r.json())
    """

    ol.create_namespace()
