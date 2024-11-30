from ..listener import Listener
from ..metadata import Metadata


class StdOutRunListener(Listener):
    def metadata_update(self, mdata: Metadata) -> None:
        print(
            f"""RUN LISTENER: {mdata.time}: {mdata.named_paths_name}.{mdata.identity} + {mdata.named_file_name} >> {mdata.run_home} """
        )
