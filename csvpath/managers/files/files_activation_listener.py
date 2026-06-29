import threading

from csvpath import CsvPaths
from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener


class FileActivationListener(Listener, threading.Thread):
    def __init__(self, *, config=None):
        Listener.__init__(self, config=config)
        threading.Thread.__init__(self)
        # self.csvpaths = None
        #
        # we hold csvpaths on the main thread, but we may not want
        # the csvpaths that triggered this listener activity and
        # shouldn't need it. we'll create our own and not having a
        # csvpaths property means we won't receive a ref to the
        # overall csvpaths context.
        #
        self.my_csvpaths = None
        self.result = None
        self.metadata = None

    def run(self):
        self._metadata_update(self.metadata)
        self.my_csvpaths.wrap_up()

    def metadata_update(self, mdata: Metadata) -> None:
        self.metadata = mdata
        self.my_csvpaths = CsvPaths()
        self.start()

    def _metadata_update(self, mdata: Metadata) -> None:
        #
        # cannot set a new CsvPaths here. crosses qt thread lines and
        # causes a segfault. move ahead of start and/or use listener's
        # own csvpaths. better the former because it is more like what
        # we have today.
        #
        activator = self.my_csvpaths.file_manager.activator
        ref = mdata.named_file_ref
        self.my_csvpaths.logger.info(
            f"Activating for {ref} if any activation is configured"
        )
        activator.activate_if(ref)
        self.my_csvpaths.logger.info(f"Activation for {ref} if any completed")
