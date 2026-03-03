import traceback
import tempfile
import os
import shutil

from smart_open import open as smart_open

import pyarrow as pa
import pyarrow.parquet as pq

from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.matching.productions import Term, Variable, Header
from csvpath.matching.functions.validity.line import Line
from csvpath.matching.functions.function import Function
from ..function_focus import MatchDecider, SideEffect
from ..args import Args
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from csvpath.matching.util.parquet_utility import ParquetUtility as paut


class Parquet(Line, SideEffect, MatchDecider):
    def check_valid(self) -> None:
        super().check_valid()
        #
        # overwrite the description
        #
        self.description = [
            self.wrap(
                """\
                Generate Parquet files containing entities defined in the same way as
                with line().

                As a subclass of Line, the parquet() is a schema construction tool. However,
                parquet() also has the function of outputing its valid entities as .parquet files
                in the run dir. Lines that don't match will not be written to the .parquet. You
                may define as many parquet() entity as needed.

                Using parquet() differs from line() in the following ways:

                * parquet() must have an unique arbitrary name qualifier

                * blank() are stored as BYTE_ARRAY

                * blank() must have a name qualifier or a header name

                * header indexes may only be used if the type has a name qualifier

                * wildcard() are simply ignored

                A parquet() might look like:

                parquet.person( string.firstname(#0), string.lastname(#1) )

                This will create a file called person.parquet in the result's run dir. In the
                case of a one-off run using CsvPath, rather than CsvPaths, the .parquet file
                will be created in the working directory.

                Note that if you use CsvPath.next() or CsvPaths.next_paths() or
                CsvPaths.next_by_line() you are responsible for calling flush() at the end of
                the run in order to make sure all matched lines are flushed to the .parquet
                file. When using CsvPaths next() methods use the csvpath_instances property to
                flush each CsvPath in turn.
                """
            ),
        ]
        #
        # super already validated siblings did check_valid. we just need to apply any more
        # specific rules spelled out in the description.
        #
        c = self.matcher.csvpath
        config = c.config
        self.batch_size = int(
            config.get(section="parquet", name="batch_size", default=25000)
        )
        self.writer = None
        self.tmp_path = None  # the path to the temp file we write to before copying to whichever backend
        self.schema = None
        try:
            self.schema = paut.line_to_schema(self)
        except ChildrenException as ex:
            msg = str(ex)
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise
        except Exception as ex:
            msg = f"Error: {ex}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise ChildrenException(msg)
        name = self.first_non_term_qualifier()
        if name is None:
            msg = "There must be a name qualifier for a parquet()"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise ChildrenException(msg)
        #
        # what if we checked here for a parquet result listener that would cleanup any
        # remaining rows? is there a better way? added a flush() capability to CsvPaths
        # we'll register a flush callable here and call it behind the scenes for
        # collect and fast_forward. people using next will need to call it for themselves.
        # this works for CsvPath and CsvPaths. using a listener would have only worked for
        # CsvPaths.
        #
        self.parquet_file_path = self._get_path()
        self.matcher.csvpath.register_flush_callback(self._flush)
        #

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        super()._decide_match(skip=skip)
        #
        # line() is always true. it relies on its children to block matches. makes sense
        # for line() but parquet() needs to make that determination itself for its own
        # functionality. i.e. we want parquet() to not write invalid lines.
        #
        guard1 = self.my_children_match()
        guard2 = self.line_matches(increase=False)
        guard = guard1 if self.nocontrib else guard2

        if guard is True:
            self._assure_writer()
            ename = f"_{self.first_non_term_qualifier()}_entity"
            #
            # capture lines to a list var buffer
            #
            entity = self.matcher.get_variable(ename, set_if_none=[])
            sibs = self.siblings()
            #
            # index_name is the count of how many rows we have. it must be
            # less than the batch size -- if not, the batch is written out.
            #
            index_name = f"_{self.first_non_term_qualifier()}_index"
            row = {}
            for i, s in enumerate(sibs):
                #
                # we don't take wildcards, so the number of sibs will often be higher
                #
                if i >= len(self.schema.names):
                    break
                v = s.to_value(skip=skip)
                row[self.schema.names[i]] = v
            entity.append(row)
            rows = self.matcher.get_variable(index_name, set_if_none=0)
            rows += 1
            if rows >= self.batch_size:
                #
                # store batch lines.
                #
                self._write(entity)
                rows = 0
                #
                # we store the entity because CsvPath converts lists to tuples at the end of
                # runs. here we shouldn't be dealing with that, but for consistency we'll
                # make the extra effort, since we can't clear the list in _write().
                #
                self.matcher.set_variable(ename, value=[])
            #
            # store the new count against the batch size.
            #
            self.matcher.set_variable(index_name, value=rows)

    def _flush(self) -> None:
        ename = f"_{self.first_non_term_qualifier()}_entity"
        entity = self.matcher.get_variable(ename, set_if_none=[])
        if len(entity) > 0:
            self._write(entity)
        try:
            self.writer.close()
            with open(self.tmp_path, "rb") as src, DataFileWriter(
                path=self.parquet_file_path, mode="wb"
            ) as dst:
                shutil.copyfileobj(src, dst.sink)
        except Exception as e:
            msg = f"Cannot save parquet file: {e}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
        finally:
            os.unlink(self.tmp_path)
            self.writer = None
            self.tmp_path = None

    def _get_path(self) -> str:
        pname = f"{self.first_non_term_qualifier()}.parquet"
        if self.matcher.csvpath.csvpaths:
            mdata = self.matcher.csvpath.csvpaths.run_metadata
            if mdata is None:
                raise MatchException("No run metadata available")
            rundir = mdata.run_home
            #
            # if we don't have an identity we will dump the parquet file in the run
            # dir. we don't have a reasonable way to find the index of the csvpath
            # within the results of a CsvPaths run. we could do it, but given this
            # is the first time the need has come up, and CsvPath should not fool
            # around with CsvPaths, it doesn't seem like we should rush into it now.
            #
            instance = self.matcher.csvpath.identity
            path = Nos(rundir)
            if instance:
                path = path.join(instance)
            pname = Nos(path).join(pname)
            #
            # we create this path once at validation time, and only for CsvPaths runs,
            # so there shouldn't be a file there already
            #
            if Nos(pname).exists():
                raise ValueError(f"There is already a file at {pname}")
        else:
            #
            # drop in a dir in the current working dir. putting the files in their own
            # dir makes clean up easier, which we'll need for one-off runs in FlightPath.
            # there we'll have potentially a lot of stranded parquet files that will
            # not be seen by the user and will eventually need to be removed. users
            # will be able to run csvpaths with parquet(), but will not have easy access
            # to the files unless/until run using a CsvPaths. they can of course dig up
            # their parquets by hand.
            #
            # that's a little lame. and fixable. we can work on it later.
            #
            if not Nos("parquet").dir_exists():
                Nos("parquet").makedirs()
            pname = Nos("parquet").join(pname)
        return pname

    def _write(self, entity: list) -> None:
        try:
            table = pa.Table.from_pylist(entity, schema=self.schema)
            self.writer.write_table(table)
        except Exception as e:
            msg = f"Error in write: {e}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)

    def _assure_writer(self) -> None:
        if self.writer is None:
            tmp = tempfile.NamedTemporaryFile(suffix=".parquet", delete=False)
            self.tmp_path = tmp.name
            tmp.close()
            self.writer = pq.ParquetWriter(self.tmp_path, self.schema)
