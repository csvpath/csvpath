from openlineage.client.client import OpenLineageClient
from marquez_client import MarquezClient

from ..metadata import Metadata
from ..listener import Listener
from ..ol.event import EventBuilder
from ..ol.job import JobBuilder
from ..ol.run import RunBuilder


class OpenLineageRunListener(Listener):
    def __init__(self, config=None):
        super().__init__(config)
        self.client = None  # MarquezClient(url='http://localhost:5000')
        self.ol_client = None

    def metadata_update(self, mdata: Metadata) -> None:
        if self.client is None:
            client_url = self.config._get("marquez", "base_url")
            if client_url is None:
                client_url = "http://localhost:5000"
            self.client = MarquezClient(url=client_url)
            self.ol_client = OpenLineageClient(url=client_url)
        #
        # do update here
        #
        # namespace = self.assure_namespace()
        #
        # make sure we have a job to run
        #
        # job = self.assure_job(mdata, namespace)
        #
        # make the new run
        #
        # run = (RunBuilder().build(mdata),)
        # job = (JobBuilder().build(mdata),)
        es = EventBuilder().build(mdata)
        for e in es:
            self.ol_client.emit(e)

    """
    def assure_job(self, mdata:Metadata, namespace) -> None:
        print(f"runlistenerol: checking jbb: {self.config.archive_name}, {mdata.named_paths_name}")
        job = None
        try:
            job = self.client.get_job(
                namespace_name=self.config.archive_name, job_name=mdata.named_paths_name)
        except Exception as e:
            print(f"runlistenerol: error: {e}")
        print(f"runlistenerol: assure jbb: {job}")
        if not job:
            print(f"runlistenerol: creating jbb")
            job = self.client.create_job(
                namespace_name=self.config.archive_name,
                job_type=JobType.BATCH,
                job_name=mdata.named_paths_name,
                description=mdata.identity
            )
        return job


    def create_run(self, mdata:Metadata, job):
        print(f"crate run: euuu: {mdata.uuid}")
        e = RunEvent.build( mdata )
        print(f"crate run: e: {e}")
        self.ol_client.emit(e)

    def assure_namespace(self) -> dict:
        name = self.config.archive_name
        ns = self.client.list_namespaces()
        print(f"runlistenerol: assure_ns: {ns}")
        for ns in ns["namespaces"]:
            n = ns["name"]
            print(f"runlistenerol: .... assure_ns: n = {n}")
            if name == n:
                print(f"runlistenerol: .... assure_ns: matched! n = {n}")
                return
        print(f"runlistenerol: no {name}")
        namespace = self.client.create_namespace(
            namespace_name=name,
            owner_name="csvpath",
            description="Archive namespace"
        )
        print(f"runlistenerol: done: {namespace}")
    """
