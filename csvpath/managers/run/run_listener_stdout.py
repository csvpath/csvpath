from ..listener import Listener
from ..metadata import Metadata


class StdOutRunListener(Listener):
    """this class just prints a line indicating that a run is
    starting. it is mainly used for testing"""

    def __init__(self, config=None):
        super().__init__(config)

    def metadata_update(self, mdata: Metadata) -> None:
        print(
            f"""RUN LISTENER: {mdata.time}: {mdata.named_paths_name}.{mdata.identity} + {mdata.named_file_name} >> {mdata.run_home} """
        )
