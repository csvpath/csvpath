import os
import json
import csv
from typing import NewType, List, Dict, Optional, Union
from datetime import datetime
from csvpath import CsvPath
from csvpath.matching.util.runtime_data_collector import RuntimeDataCollector
from csvpath.util.line_spooler import LineSpooler
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos

Simpledata = NewType("Simpledata", Union[None | str | int | float | bool])
"""@private"""
Listdata = NewType("Listdata", list[None | str | int | float | bool])
"""@private"""
Csvdata = NewType("Csvdata", list[List[str]])
"""@private"""
Metadata = NewType("Metadata", Dict[str, Simpledata])
"""@private"""


class ResultSerializer:
    """@private"""

    def __init__(self, base_dir: str):
        # base is the archive dir from config.ini
        self.base_dir = base_dir
        self.result = None
        self._nos = None

    @property
    def nos(self) -> Nos:
        if self._nos is None:
            self._nos = Nos(None)
        return self._nos

    def save_result(self, result) -> None:
        self.result = result
        runtime_data = {}
        result.csvpath.csvpaths.logger.debug(
            "Saving result of %s.%s", result.paths_name, result.identity_or_index
        )
        RuntimeDataCollector.collect(result.csvpath, runtime_data, local=True)
        runtime_data["run_index"] = result.run_index
        es = []
        if result is not None and result.errors:
            es = [e.to_json() for e in result.errors]
        self._save(
            metadata=result.csvpath.metadata,
            errors=es,
            variables=result.variables,
            lines=result.lines,
            printouts=result.printouts,
            runtime_data=runtime_data,
            paths_name=result.paths_name,
            file_name=result.file_name,
            identity=result.identity_or_index,
            run_time=result.run_time,
            run_dir=result.run_dir,
            run_index=result.run_index,
            unmatched=result.unmatched,
        )
        self.result = None

    def _save(
        self,
        *,
        metadata: Metadata,
        runtime_data: Metadata,
        errors: List[Metadata],
        variables: dict[str, Simpledata | Listdata | Metadata],
        lines: Csvdata,
        printouts: dict[str, list[str]],
        paths_name: str,
        file_name: str,
        identity: str,
        run_time: datetime,
        run_dir: str,
        run_index: int,
        unmatched: list[Listdata],
    ) -> None:
        """Save a single Result object to basedir/paths_name/run_time/identity_or_index."""
        meta = {
            "paths_name": paths_name,
            "file_name": file_name,
            "run_time": f"{run_time}",
            "run_index": run_index,
            "identity": identity,
            "metadata": metadata,
            "runtime_data": runtime_data,
        }
        run_dir = self.get_instance_dir(run_dir=run_dir, identity=identity)
        # Save the JSON files
        with DataFileWriter(path=os.path.join(run_dir, "meta.json")) as f:
            json.dump(meta, f.sink, indent=2)
        with DataFileWriter(path=os.path.join(run_dir, "errors.json")) as f:
            json.dump(errors, f.sink, indent=2)
        with DataFileWriter(path=os.path.join(run_dir, "vars.json")) as f:
            json.dump(variables, f.sink, indent=2)
        # Save lines returned as a CSV file. note that they may have already
        # spooled and the spooler been discarded.
        if lines is not None:
            if isinstance(lines, LineSpooler) and lines.closed is True:
                self.result.csvpath.logger.debug(
                    "line spooler has already written its data"
                )
            elif isinstance(lines, LineSpooler):
                self.result.csvpath.logger.debug(
                    "not writing data in/from line spooler even though lines.closed is not True"
                )
            else:
                #
                # this may not be right, but I think we can/maybe should not write data unless
                # we have some. that would match the possible spooler behavior. it would also
                # match fast_forward, which might be confusing, but if we capture the what method
                # a run used that's not a worry. and if we don't, not having a data file is a
                # poor indicator of the method anyway.
                #
                if lines is not None and len(lines) > 0:
                    with DataFileWriter(path=os.path.join(run_dir, "data.csv")) as f:
                        writer = csv.writer(f.sink)
                        writer.writerows(lines)
        #
        # writing is not needed. LineSpoolers are intended to stream their
        # lines to disk. if we write here we'll be reading and writing the
        # same file at the same time.
        #
        if (
            unmatched is not None
            and not isinstance(unmatched, LineSpooler)
            and len(unmatched) > 0
        ):
            with DataFileWriter(path=os.path.join(run_dir, "unmatched.csv")) as f:
                writer = csv.writer(f.sink)
                writer.writerows(unmatched)

        # Save the printout lines
        if self._has_printouts(printouts):
            with DataFileWriter(path=os.path.join(run_dir, "printouts.txt")) as f:
                for k, v in printouts.items():
                    f.sink.write(f"---- PRINTOUT: {k}\n")
                    for _ in v:
                        f.sink.write(f"{_}\n")

    def _has_printouts(self, pos) -> bool:
        if pos is None:
            return False
        if len(pos) == 0:
            return False
        for k, v in pos.items():
            if v is not None and len(v) > 0:
                return True
        return False

    def get_instance_dir(self, run_dir, identity) -> str:
        run_dir = os.path.join(run_dir, identity)
        nos = self.nos
        nos.path = run_dir
        if not nos.exists():
            nos.makedirs()
        return run_dir
