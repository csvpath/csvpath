import os
import json
from csvpath.util.exceptions import InputException


class OpenLineageListener:
    def __init__(self, config):
        self.config = config

    def metadata_update(self, mdata) -> None:
        n = {}
        p = "https://github.com/csvpath"

        n["eventTime"] = mdata["time"].strftime("%Y-%m-%dT%H:%M:%sZ")
        n["producer"] = p
        n["schemaURL"] = "https://openlineage.io/spec/0-0-1/OpenLineage.json"
        ds = {}
        n["dataset"] = ds
        ds["namespace"] = mdata["named_file_name"]
        ds["name"] = mdata["file_name"]
        fs = {}
        ds["facets"] = fs

        bf = "https://openlineage.io/spec/1-0-2/OpenLineage.json#/$defs/BaseFacet"
        f = {}
        fs["uuid"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata["uuid"]

        f = {}
        fs["origin"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata["origin"]

        f = {}
        fs["archive_path"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata["archive_path"]

        f = {}
        fs["name_home"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata["name_home"]

        f = {}
        fs["file_home"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata["file_home"]

        f = {}
        fs["fingerprint"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata["fingerprint"]

        f = {}
        fs["mark"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata["mark"]

        f = {}
        fs["type"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata["type"]

        f = {}
        fs["manifest_path"] = f
        f["producer"] = p
        f["schemaURL"] = bf
        f["value"] = mdata["manifest_path"]

        t = json.dumps(n, indent=2)
        print(f"json is: \n{t}")

        """
        with open(manifest_path, "w", encoding="utf-8") as file:
            json.dump(jdata, file, indent=2)
        """
        return n


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

    import urllib

    params = urllib.parse.urlencode(p)
    f = urllib.urlopen("http://localhost:5000/api/v1/lineage", params)
    print(f.read())
