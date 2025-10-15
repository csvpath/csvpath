import os
import subprocess
import threading
from datetime import datetime, timezone
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.exceptions import CsvPathsException
from csvpath.util.box import Box
from csvpath.util.nos import Nos


class ScriptsResultsListener(Listener, threading.Thread):
    def __init__(self, config=None):
        Listener.__init__(self, config=config)
        threading.Thread.__init__(self)
        self.csvpaths = None

    def run(self):
        #
        # csvpath adds its config, but under it's thread's name, so we
        # have to do it again here.
        #

        #
        # exp: replace Csvpaths so we have all new everything. we didn't need the old
        # one's state and its state may have poluted threads.
        #
        # update: this experiment is not ok for a server env. the only way we know where
        # we are is by looking at config.configpath. creating a new csvpaths obj breaks
        # that. we don't need to do it, but if ever needed we can copy configpath into a
        # new csvpaths obj.
        #
        # from csvpath import CsvPaths
        #
        # self.csvpaths = CsvPaths()
        #
        Box().add(Box.CSVPATHS_CONFIG, self.csvpaths.config)
        self._metadata_update(self.metadata)
        self.csvpaths.wrap_up()
        Box().empty_my_stuff()

    def metadata_update(self, mdata: Metadata) -> None:
        self.metadata = mdata
        #
        # we should be doing this here because why create a thread if not needed
        # but atm debugging something else.
        #
        run = self.csvpaths.config.get(section="scripts", name="run_scripts")
        if run is None or run.strip() not in ["on", "true", "yes"]:
            self.csvpaths.logger.info(
                "Not running completion scripts, if any, because run_scripts is not yes"
            )
            return
        self.start()

    def _metadata_update(self, mdata: Metadata) -> None:
        #
        # create separate csvpaths instance here on the thread?
        #
        if not self.csvpaths:
            raise RuntimeError("Scripts results listener requires a CsvPaths instance")
        if mdata.time_completed is None:
            return
        #
        # if we set a flag to run scripts we will, if any. otherwise, we skip.
        #
        run = self.csvpaths.config.get(section="scripts", name="run_scripts")
        if run is None or run.strip() not in ["on", "true", "yes"]:
            self.csvpaths.logger.info(
                "Not running completion scripts, if any, because run_scripts is not yes"
            )
            return
        #
        # find any scripts
        #
        pm = self.csvpaths.paths_manager
        cfg = None
        cfg = pm.get_config_for_paths(mdata.named_paths_name)
        if cfg is None:
            return
        #
        # all runs for every execution, regardless of completeness, validity, etc.
        #
        t = "on_complete_all_script"
        all_script = cfg.get(t)
        if all_script is not None and all_script.strip() != "":
            self._run(mdata=mdata, script_name=all_script, script_type=t)
        #
        # valid and invalid run according to the mdata:
        #   self.all_valid: bool = None
        #   self.error_count: int = None
        #
        if mdata.all_valid is True:
            t = "on_complete_valid_script"
            valid_script = cfg.get(t)
            if valid_script is not None and valid_script.strip() != "":
                self._run(mdata=mdata, script_name=valid_script, script_type=t)
        else:
            t = "on_complete_invalid_script"
            invalid_script = cfg.get(t)
            if invalid_script is not None and invalid_script.strip() != "":
                self._run(mdata=mdata, script_name=invalid_script, script_type=t)
        if mdata.error_count > 0:
            t = "on_complete_error_script"
            error_script = cfg.get(t)
            if error_script is not None and error_script.strip() != "":
                self._run(mdata=mdata, script_name=error_script, script_type=t)

    def _run(self, *, mdata, script_name, script_type) -> None:
        #
        # get the script's bytes
        # write to a temp file
        # execute the file catching system out
        # write system out to a script_name-timestamp.txt file in the results dir
        #
        try:
            b = self.csvpaths.paths_manager.get_script_for_paths(
                name=mdata.named_paths_name, script_type=script_type
            )
            path = os.path.dirname(mdata.manifest_path)
            path = Nos(path).join(script_name)
            with DataFileWriter(path=path) as file:
                file.write(b)
            #
            # below is supposedly cross platform but just in case.
            #
            try:
                os.chmod(path, 0o755)
            except Exception:
                ...
            print(f"runningx: path: {[path]}")
            result = subprocess.run([path], capture_output=True, text=True, check=True)
            out = result.stdout
            err = result.stderr
            if err is not None and err.strip() != "":
                out = f"{out}\n ===================== \n{err}"
            n = datetime.now(timezone.utc)
            script_out_name = f"{script_name}-{n.strftime('%Y-%m-%d_%H-%M-%S_%f')}.txt"
            script_out_path = mdata.run_home
            script_out_path = Nos(script_out_path).join(script_out_name)
            # script_out_path = os.path.join(script_out_path, script_out_name)
            with DataFileWriter(path=script_out_path) as file:
                file.write(out)
        except Exception as e:
            msg = f"Run script failed on results {mdata.named_paths_name}, script_name {script_name}, with {type(e)}: {e}"
            self.csvpaths.logger.error(msg)
            if self.csvpaths.ecoms.do_i_raise():
                raise RuntimeError(msg) from e
