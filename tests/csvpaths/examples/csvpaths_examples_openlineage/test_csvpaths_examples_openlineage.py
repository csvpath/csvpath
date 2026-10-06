import unittest
from uuid import uuid4
import json
import os

from openlineage.client.serde import Serde
from openlineage.client.generated.base import EventType

from csvpath import CsvPaths
from csvpath.managers.integrations.ol.v2.builders.event import EventBuilder
from csvpath.managers.integrations.ol.v2.sender import Sender
from csvpath.managers.files.file_metadata import FileMetadata

FILE = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_openlineage",
    "csvs/March-2024.csv",
)
PATHS = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_openlineage",
    "csvpaths",
    "hello_world.csvpath",
)


class TestCsvPathsExamplesOpenLineage(unittest.TestCase):
    def test_csvpaths_openlineage_files_1(self) -> None:
        paths = CsvPaths()
        mdata = FileMetadata(paths.config)
        mdata.named_file_name = "orders"
        mdata.named_files_root = "/Users/me/csvpath/named_entities/files"
        mdata.origin_path = "x/y/z.json"
        mdata.template = ":0/:filename"
        mdata.uuid_string = str(uuid4())
        mdata.status = "Registration failed"
        mdata.file_path = "tmp/local/inputs/named_files/orders/x/z.json"

        sender = Sender()
        sender.csvpaths = paths

        es = EventBuilder(listener=sender).build(mdata)
        assert es is not None
        assert len(es) == 2
        start = es[0]
        complete = es[1]

        from csvpath.util.code import Code

        p = Code.get_source_path(start.__class__)
        print(f"p: {p}")

        print("\nSTART: ")
        je = Serde.to_json(start)
        obj = json.loads(je)
        s = json.dumps(obj, indent=4)
        print(s)

        print("\nCOMPLETE: ")
        je = Serde.to_json(complete)
        obj = json.loads(je)
        s = json.dumps(obj, indent=4)
        print(s)

        assert start.eventType == EventType.START
        assert complete.eventType == EventType.COMPLETE

        job = start.job
        assert job
        assert job.facets
        assert len(job.facets) == 2
        ttype = job.facets.get("jobType")
        assert ttype.integration == "CSVPATH"
        assert ttype.jobType == "REGISTER"
        assert ttype.processingType == "BATCH"
        assert not start.outputs
        assert start.inputs

    def test_csvpaths_openlineage_files_2(self) -> None:
        paths = CsvPaths()
        ref, mdata = paths.file_manager.add_named_file(
            name="orders", path=FILE, return_metadata=True
        )

        sender = Sender()
        sender.csvpaths = paths

        es = EventBuilder(listener=sender).build(mdata)
        assert es is not None
        assert len(es) == 2
        start = es[0]
        complete = es[1]

        from csvpath.util.code import Code

        p = Code.get_source_path(start.__class__)
        print(f"p: {p}")

        print("\nSTART: ")
        je = Serde.to_json(start)
        obj = json.loads(je)
        s = json.dumps(obj, indent=4)
        print(s)

        print("\nCOMPLETE: ")
        je = Serde.to_json(complete)
        obj = json.loads(je)
        s = json.dumps(obj, indent=4)
        print(s)

    def test_csvpaths_openlineage_files_3(self) -> None:
        paths = CsvPaths(project="unit", project_context="testing")
        paths.config.set(
            section="listeners", name="openlineage.namespace", value="project"
        )
        paths.config.set(section="listeners", name="openlineage.version", value="2")
        paths.config.set(section="listeners", name="groups", value="openlineage")
        ref, mdata = paths.file_manager.add_named_file(
            name="orders", path=FILE, return_metadata=True
        )

    #
    # ========================================
    #
    def test_csvpaths_openlineage_paths_1(self) -> None:
        paths = CsvPaths(project="unit", project_context="testing")
        paths.config.set(
            section="listeners", name="openlineage.namespace", value="project"
        )
        paths.config.set(section="listeners", name="openlineage.version", value="2")
        paths.config.set(section="listeners", name="groups", value="openlineage")

        ref, mdata = paths.paths_manager.add_named_paths(
            name="orders", from_file=PATHS, return_metadata=True
        )

        sender = Sender()
        sender.csvpaths = paths

        es = EventBuilder(listener=sender).build(mdata)
        assert es is not None
        assert len(es) == 1
        complete = es[0]

        print("\nCOMPLETE: ")
        je = Serde.to_json(complete)
        obj = json.loads(je)
        s = json.dumps(obj, indent=4)
        print(s)

    #
    #
    # ======================================
    #

    def test_csvpaths_openlineage_results_1(self) -> None:
        paths = CsvPaths()
        paths.config.set(
            section="listeners", name="groups", value="default, openlineage"
        )
        paths.config.set(section="listeners", name="openlineage.version", value="2")

        ref, mdata = paths.file_manager.add_named_file(
            name="orders", path=FILE, return_metadata=True
        )
        ref, mdata = paths.paths_manager.add_named_paths(
            name="orders", from_file=PATHS, return_metadata=True
        )

        metadatas = []
        paths.collect_paths(filename="orders", pathsname="orders", metadatas=metadatas)
        #
        # start metadata
        #
        # mdata = paths.run_metadata
        #
        # complete metadata
        #
        mdata = metadatas[-1]

        sender = Sender()
        sender.csvpaths = paths

        es = EventBuilder(listener=sender).build(mdata)
        assert es is not None
        assert len(es) == 1
        start = es[0]

        print("\nEVENT: ")
        je = Serde.to_json(start)
        obj = json.loads(je)
        s = json.dumps(obj, indent=4)
        print(s)

    #
    #
    # =======================================
    #

    def test_csvpaths_openlineage_result_1(self) -> None:
        paths = CsvPaths()
        paths.config.set(
            section="listeners", name="groups", value="default, openlineage"
        )
        paths.config.set(section="openlineage", name="version", value="2")
        # paths.config.set(section="openlineage", name="base_url", value="")

        ref, mdata = paths.file_manager.add_named_file(
            name="orders", path=FILE, return_metadata=True
        )
        ref, mdata = paths.paths_manager.add_named_paths(
            name="orders", from_file=PATHS, return_metadata=True
        )
        #
        # we have the run's overall metadata from the csvpaths (below)
        # here we're going to pass in a list and get metadata tuples for
        # every statement. tuples are: (RunMetadata, ResultMetadata)
        #
        metadatas = []
        results = []
        paths.collect_paths(
            filename="orders", pathsname="orders", metadatas=metadatas, results=results
        )
        mdata = paths.run_metadata
        print(f"mdata: {mdata}")
        print(f"results: {results}")
        print(f"mdatas: {metadatas}")
        assert len(metadatas) > 0
        assert len(results) > 0

        sender = Sender()
        sender.csvpaths = paths
        #
        # first statement's ResultMetadata
        #
        # mdata = metadatas[0][1]
        mdata = results[0].result_metadata
        print(
            f"COMPLETED: {mdata.completed}, {mdata.time_completed_string}, {id(mdata)}"
        )

        es = EventBuilder(listener=sender).build(mdata)
        assert es is not None
        assert len(es) >= 1
        start = es[0]

        print("\nEVENT:\n ")
        je = Serde.to_json(start)
        obj = json.loads(je)
        s = json.dumps(obj, indent=4)
        print(s)
