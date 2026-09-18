import threading
import json
import io

from typing import Any, NewType, Optional
from uuid import uuid4

from pandas import DataFrame
import jsonlines


from csvpath.util.run_home_maker import RunHomeMaker
from csvpath.managers.results.result import Result

from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.runners.runner import Runner

# types for clarity
Reference = NewType("Reference", str)


class CollectDynamic(Runner):
    def register_if(
        self,
        *,
        data: Any,
        dataname: str,
        register_path: str,
        shape: str = "json",
        register_template=None,
    ):
        if not self.csvpaths.file_manager.has_named_file(dataname):
            placeholder = "Placeholder"
            if shape == self.JSONL:
                placeholder = {"name": placeholder}
            self.register(
                data=placeholder,
                dataname=dataname,
                register_path=register_path,
                shape=shape,
                register_template=register_template,
            )

    def register(
        self,
        *,
        data: Any,
        dataname: str,
        register_path: str,
        shape: str = "json",
        register_template=None,
    ):
        tid = threading.get_ident()
        if isinstance(data, DataFrame):
            register_path = f"{register_path}-{tid}.jsonl"
            datastr = data.to_json(orient="records", lines=True)
            with DataFileWriter(path=register_path, mode="w") as writer:
                writer.write(datastr)
        elif shape == self.JSON:
            register_path = f"{register_path}-{tid}.{shape}"
            with DataFileWriter(path=register_path, mode="w") as writer:
                json.dump(data, writer.sink)
        elif shape == self.JSONL:
            register_path = f"{register_path}-{tid}.{shape}"
            datastr = io.StringIO()
            with jsonlines.Writer(datastr) as writer:
                writer.write_all(data)
            with DataFileWriter(path=register_path, mode="w") as writer:
                writer.write(datastr.getvalue())
        elif shape == self.LIST_OF_JSON:
            register_path = f"{register_path}-{tid}.json"
            for _ in data:
                with DataFileWriter(path=register_path, mode="w") as writer:
                    json.dump(_, writer.sink)
                    self.csvpaths.file_manager.add_named_file(
                        name=dataname, path=register_path, template=register_template
                    )
            Nos(register_path).remove()
            return
        #
        # do the registration
        #
        self.csvpaths.file_manager.add_named_file(
            name=dataname, path=register_path, template=register_template
        )
        #
        # delete the temp file. we don't use a TemporaryFile because
        # the user decides where to locate it, in order to allow the use
        # of templates. We add a thread ID to the name, so it's not 100%
        # under their control, but for the purpose of organizing the
        # data space it will work.
        #
        Nos(register_path).remove()

    #
    # data: the value to be processed, essentially the content of an unregistered file
    # template: a string that determines the position of the run_dir
    # pathsname: the name of the named-paths group that will be used to process the data
    # shape: instruction as to how to treat the data, one of: json, jsonl, listof (json)
    # extra_data: metadata to be stored with the results
    #
    def run(
        self,
        *,
        data: dict | list,
        pathsname: str,
        dataname: str,
        dataname_trust=False,  # if not registering we still need a dummy named-file
        register=False,
        register_template=None,
        register_path=None,
        run_template: str = None,
        extra_data: Optional[dict[str, str]] = None,
        shape: str = Runner.JSON,
    ) -> list[Reference]:
        #
        # caching should never help us
        #
        caching = self.csvpaths.config.get(section="cache", name="use_cache")
        self.csvpaths.config.set(section="cache", name="use_cache", value="no")

        self.not_none(data, "Data cannot be None")
        self.not_empty(data, "Data cannot be empty")

        self.not_none(pathsname, "Pathsname cannot be None")
        self.not_empty(pathsname, "Pathsname cannot be empty")

        self.not_shape(shape)

        #
        # getting the last file registered can be expensive. passing in
        # register_path prevents that. otoh, if we're not registering and
        # we're trusting that the named-file is available, we don't have
        # that problem.
        #
        # if we use templates we must have an "original" source path to
        # apply to the templates. in quotes because since this is a dynamic
        # run it is not an actual file path, just a path used for templates.
        #
        if (run_template or register_template) and register_path is None:
            raise ValueError(
                "Cannot use templates when there is no register path to merge with them"
            )
        if register is True and register_path is None:
            register_path = "unnamed bytes"
        if register is True:
            self.register(
                data=data,
                dataname=dataname,
                shape=shape,
                register_path=register_path,
                register_template=register_template,
            )
        elif dataname_trust is False:
            self.register_if(
                data=data,
                dataname=dataname,
                shape=shape,
                register_path=register_path,
                register_template=register_template,
            )
        else:
            ...  # anything here?

        #
        # we need a named-file so that we have the ability to use
        # templates. if the user added a named-file already and we're
        # not registering this run, we just take the last dataname
        # (named-file name). if we're registering we need a path, but
        # the path can be just the file name with a slash in front,
        # which we can do ourselves back here.
        #
        refs = []
        #
        #
        #
        if isinstance(data, (list, tuple)) and shape == self.LIST_OF_JSON:
            for d in data:
                ref = self._collect_dynamic(
                    pathsname=pathsname,
                    dataname=dataname,
                    template=run_template,
                    data=d,
                    shape=self.JSON,
                    extra_data=extra_data,
                )
                refs.append(ref)
        elif isinstance(data, (list, tuple, dict)) and shape in [
            self.JSONL,
            self.DATA_FRAME,
        ]:
            #
            # JSONL
            #
            if isinstance(data, dict):
                data = [data]
            ref = self._collect_dynamic(
                pathsname=pathsname,
                dataname=dataname,
                template=run_template,
                data=data,
                shape=self.JSONL,
                extra_data=extra_data,
            )
            refs.append(ref)
        elif isinstance(data, (list, tuple, dict)) and shape == self.JSON:
            refs = self._collect_dynamic(
                pathsname=pathsname,
                dataname=dataname,
                template=run_template,
                data=data,
                shape=self.JSON,
                extra_data=extra_data,
            )
            refs.append(ref)
        else:
            raise ValueError("Incorrect data and/or shape: {data}, {shape}")
        #
        # probably won't matter but replace caching
        #
        self.csvpaths.config.set(section="cache", name="use_cache", value=caching)

        return refs

    def _collect_dynamic(
        self,
        *,
        pathsname: str,
        data: dict | list,
        shape: str,
        dataname: str,
        template: str = None,
        extra_data: Optional[dict[str, str]] = None,
    ) -> Reference:
        #
        # if template is None we need to go find any template that was given when
        # the named-paths were loaded.
        #
        file = self.csvpaths.file_manager.get_named_file(name=dataname)
        if file is None:
            raise ValueError("There must, at minimum, be a placeholder named-file")
        paths = self.csvpaths._get_named_paths(pathsname)
        if template is None:
            template = self.csvpaths.paths_manager.get_template_for_paths(pathsname)
        self.csvpaths.logger.info(
            "Prepping %s and %s with template %s", dataname, pathsname, template
        )
        self.csvpaths.clean(paths=pathsname)
        self.csvpaths.logger.info(
            "Beginning collect_dynamic %s with %s paths using template %s",
            pathsname,
            len(paths),
            template,
        )
        #
        # this sets up the DataFileReader to recognize that we have live
        # data, not a file, and load the correct reader. the actual dynamic
        # json readers know how to find their data.
        #
        # we have a file -- the named-file must have at least one registered
        # placeholder. we use that file path as the key to register the
        # dynamic data. so it looks like we're going after a file, but the
        # DataFileReader checks for dynamic json/data frames before looking
        # at actual files.
        #
        # the data and the shape indicators are stored in a box's thread
        # local dict for the current thread. CsvPaths clears out the box
        # when we're done with this run.
        #
        DataFileReader.register_data(path=file, data=data, shape=shape)

        #
        # run identification and directories created here
        #
        maker = RunHomeMaker(self.csvpaths)
        crt = maker.get_run_dir(
            paths_name=pathsname, file_name=dataname, template=template
        )
        #
        # capture the last run dir for the benefit of the caller
        #
        self.csvpaths._last_run_dir = crt

        results = []
        #
        # adding uuid for the run as a whole
        run_uuid = uuid4()
        #
        # run starts here
        #
        self.csvpaths.run_metadata = self.csvpaths.results_manager.start_run(
            run_dir=crt,
            pathsname=pathsname,
            filename=dataname,
            file=file,
            run_uuid=run_uuid,
            method="collect_dynamic",
            template=template,
            extra_data=extra_data,
        )
        #
        #
        #
        for i, path in enumerate(paths):
            csvpath = self.csvpaths.csvpath()
            if not csvpath.will_run:
                continue
            result = Result(
                csvpath=csvpath,
                file_name=dataname,
                paths_name=pathsname,
                run_index=i,
                run_time=self.csvpaths.current_run_time,
                run_dir=crt,
                run_uuid=run_uuid,
                method="collect_dynamic",
                template=template,
            )
            # casting a broad net because if "raise" not in the error policy we
            # want to never fail during a run
            try:
                self.csvpaths._load_csvpath(
                    csvpath=csvpath,
                    path=path,
                    file=dataname,
                    pathsname=pathsname,
                    filename=dataname,
                    crt=crt,
                    index=i,
                )
                #
                # if run-mode: no-run we skip ahead without saving results
                #
                if not csvpath.will_run:
                    continue
                #
                # the add has to come after _load_csvpath because we need the identity or index
                # to be stable and the identity is found in load, if it exists.
                #
                self.csvpaths.results_manager.add_named_result(result)
                lines = result.lines
                self.csvpaths.logger.debug("Collecting lines using a %s", type(lines))
                csvpath.collect(lines=lines)
                if lines is None:
                    self.logger.error(  # pragma: no cover
                        "Unexpected None for lines after collect_dynamic: file: %s, match: %s",
                        dataname,
                        csvpath.match,
                    )
                #
                # TODO: unmatched needs additional support for streaming very large files
                #
                result.unmatched = csvpath.unmatched
            except Exception as ex:  # pylint: disable=W0718
                if self.csvpaths.error_manager.csvpaths is None:
                    raise Exception("ErrorManager's CsvPaths cannot be None")
                self.csvpaths.error_manager.handle_error(source=self, msg=f"{ex}")
                if self.csvpaths.ecoms.do_i_raise():
                    self.csvpaths.results_manager.save(result)
                    raise
            self.csvpaths.results_manager.save(result)
            results.append(result)
        #
        # run ends here
        #
        self.csvpaths.results_manager.complete_run(
            run_dir=crt, pathsname=pathsname, results=results
        )
        #
        # update/write run manifests here
        #  - validity (are all paths valid)
        #  - paths-completeness (did they all run and complete)
        #  - method (collect, fast_forward, next)
        #  - timestamp
        #
        self.csvpaths.clear_run_coordination()
        self.csvpaths.logger.info(
            "Completed collect_dynamic %s with %s paths", pathsname, len(paths)
        )
        if self.csvpaths.wrap_up_automatically:
            self.csvpaths.wrap_up()
        #
        # the run home is the most specific reference we can return
        #
        # return f"${pathsname}.results.{crt}"
        ret = self.csvpaths._make_run_reference(pathsname=pathsname, crt=crt)

        return ret
