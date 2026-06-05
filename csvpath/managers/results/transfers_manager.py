import traceback
from csvpath.util.exceptions import InputException
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.managers.paths.paths_descriptor import Transfer, Transfers

from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu


class TransfersManager:
    def __init__(self, *, results_manager):
        self._results_manager = results_manager

    @property
    def csvpaths(self):
        return self.results_manager.csvpaths

    @property
    def results_manager(self):
        return self._results_manager

    def do_transfers_if(self, result) -> None:
        try:
            self.do_transfer_mode_if(result)
        except Exception as ex:
            #
            # handle better!
            #
            print(traceback.format_exc())
            self.results_manager.csvpaths.logger.error(ex)
        try:
            self.do_description_transfers_if(result)
        except Exception as ex:
            #
            # handle better!
            #
            print(traceback.format_exc())
            self.results_manager.csvpaths.logger.error(ex)

    def do_description_transfers_if(self, result) -> None:
        #
        # this is the new way to do transfers: config in paths description file.
        # it allows for N-transfers per csvpath, with those transfers triggered
        # by end run state: all, valid, invalid, error.
        #
        csvpaths = self.results_manager.csvpaths
        pathsmgr = csvpaths.paths_manager
        name = result.paths_name
        describer = pathsmgr.describer
        transfers = describer.get_transfers(name)
        #
        # atm we always plan to have transfers object, but we can test for it
        # regardless.
        #
        if transfers and transfers.path_transfers is not None:
            #
            # we only allow transfers to be defined on the index if there is no
            # identity. otherwise, an index will not match.
            #
            n = result.identity_or_index
            if n is not None and n in transfers.path_transfers:
                self.do_description_transfers(
                    result, name, transfers.path_transfers.get(n)
                )

    def do_description_transfers(self, result, name: str, t: Transfers) -> None:
        ts = t.on_complete_all
        for _ in ts:
            self.do_description_transfer(result, name, _)
        if result.is_valid:
            ts = t.on_complete_valid
            for _ in ts:
                self.do_description_transfer(result, name, _)
        else:
            ts = t.on_complete_all
            for _ in ts:
                self.do_description_transfer(result, name, _)
        if result.has_errors():
            ts = t.on_complete_all
            for _ in ts:
                self.do_description_transfer(result, name, _)

    def do_description_transfer(self, result, name: str, t: Transfer) -> None:
        #
        # alternately, we could do all at once from a single array, either way.
        #
        tpaths = self._transfer_paths(result, [(t.file, t.transfer_to)])
        self._do_transfers(tpaths, name)

    def do_transfer_mode_if(self, result) -> None:
        #
        # this code fork is the old way. transfer mode is one of the modes that can
        # be set in the leading comment of a csvpath running in a csvpaths group. it
        # is more limited in that it only has the one state -- always runs.
        #
        # for now we are keeping it on the grounds that a mode may be helpful during
        # testing, and maybe even as a separate capability in a prod env; tho i'm not
        # sure i can think of the slam-book case.
        #
        transfers = result.csvpath.transfers
        if transfers is None:
            return
        tpaths = self.transfer_paths(result)
        self._do_transfers(tpaths, result.paths_name)

    def _name_for_token(self, result, nametoken) -> tuple[str, str]:
        file = None
        if nametoken is None:
            raise ValueError("Nametoken cannot be None")
        nametoken = nametoken.strip()
        if nametoken == "source":
            name = result.file_name
            fmgr = self.csvpaths.file_manager
            file = fmgr.get_named_file(name)
            base = self.csvpaths.config.get(section="inputs", name="files")
            if not file.startswith(base):
                file = file.lstrip("/")
                file = file.lstrip("\\")
                file = f"{base}{Nos(base).sep}{file}"
        elif nametoken.startswith("data"):
            file = "data.csv"
        elif nametoken.startswith("unmatched"):
            file = "unmatched.csv"
        elif nametoken.startswith("printouts"):
            file = "printouts.txt"
        elif nametoken.startswith("vars"):
            file = "vars.json"
        elif nametoken.startswith("errors"):
            file = "errors.json"
        elif nametoken.startswith("manifest"):
            file = "manifest.json"
        elif nametoken.startswith("meta"):
            file = "meta.json"
        elif nametoken.endswith(".md"):
            file = nametoken
        elif nametoken.endswith(".parquet"):
            file = nametoken
        elif nametoken.endswith(".txt"):
            file = nametoken
        elif nametoken.endswith(".csv"):
            file = nametoken
        elif nametoken.endswith(".json"):
            file = nametoken
        else:
            msg = f"Unknown transfer: {nametoken}. Must be data, unmatched, source, csv, .json, .parquet, .md, .txt"
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            raise ValueError(msg)
        return file

    def _mode_for_name_and_var(self, file, var) -> str:
        if var.endswith("+"):
            return "a"
        elif file.endswith(".parquet"):
            return "wb"
        return "w"

    def transfer_paths(self, result) -> list[tuple[str, str, str, str, str]]:
        #
        # 1: filename, no extension needed: data | unmatched
        # 2: variable name containing the path to write to
        # 3: path of source file
        # 4: path to write to
        #
        transfers = result.csvpath.transfers
        return self._transfer_paths(result, transfers)

    def _transfer_paths(
        self, result, transfers: list[tuple[str, str]]
    ) -> list[tuple[str, str, str, str, str]]:
        #
        # 1: filename, no extension needed: data | unmatched
        # 2: variable name containing the path to write to
        # 3: path of source file
        # 4: path to write to
        #
        tpaths = []
        for t in transfers:
            _ = self._names_and_paths(result, t[0], t[1])
            tpaths.append(_)
        return tpaths

    def _names_and_paths(
        self, result, filename, varname
    ) -> tuple[str, str, str, str, str]:
        # (filefrom, varname, pathfrom, pathto, mode)

        filefrom = self._name_for_token(result, filename)
        mode = self._mode_for_name_and_var(filefrom, varname)
        #
        # in the case of "source" we have the fully qualified path to the source file
        # so we don't need to construct a from path.
        #
        pathfrom = (
            filefrom if filename == "source" else self._path_to_result(result, filefrom)
        )
        varname = varname.rstrip("+")
        pathto = self._path_to_transfer_to(result, varname)
        #
        # here we're doing a set/get in order to have var sub. that means
        # that if we are transferring to a ALL_CAPS var name the env var
        # will be used. HOWEVER: that is bad because then a writer can
        # attach an admin's env vars and send them somewhere they will be
        # logged, e.g. an sftp server failure logged. BUT, in the case of
        # OS env for FlightPath Data, we don't care because we own the
        # machine. and for FlightPath Server, we don't care because
        # projects own their env.json files so they aren't privledged; OS
        # env offlimits already. leaving progammatic use of the library
        # do we care to protect devs using CsvPath lib from this kind of
        # own-foot-shooting? we could check with config.ini [results] for
        # a [results] transfers_var_sub with a default of False. TBD.
        #
        if pathto:
            result.csvpath.config.set(
                section="_dummy-section", name="_dummy-name", value=pathto
            )
            pathto = result.csvpath.config.get(
                section="_dummy-section", name="_dummy-name"
            )
            #
            #
            #
        return (filefrom, varname, pathfrom, pathto, mode)

    def _do_transfers(self, tpaths, name: str) -> None:
        for t in tpaths:
            pathfrom = t[2]
            pathto = t[3]
            try:
                rmode = "rb" if "b" in t[4] else "r"
                n = pathu.dir_name(pathto)
                nos = Nos(n)
                if not nos.dir_exists():
                    nos.makedirs()

                nos = Nos(pathfrom)
                #
                # use named-paths descriptor server configs to allow transfer to otherwise unknown SFTP servers
                #
                with DataFileReader(pathfrom, mode=rmode) as pf:
                    #
                    # adding config to the reader allows the reader to look to the config for
                    # server credentials that match host and port, if any. this capability is
                    # only used for transfers and the writer only looks in named-paths
                    # descriptor
                    #
                    writer = DataFileWriter(path=pathto, mode=t[4])
                    try:
                        config = self.csvpaths.paths_manager.describer.get_config(name)
                        servers = config.destinations
                        writer.server_config = servers
                        writer.load_if()
                        writer.sink.write(pf.read())
                    finally:
                        writer.close()
            except Exception:
                print(traceback.format_exc())
                logger = self.results_manager.csvpaths.logger
                logger.warning(
                    "Cannot transfer %s to %s", pathfrom, pathto, exc_info=True
                )

    def _path_to_transfer_to(self, result, t) -> str:
        if result is None:
            raise ValueError("Result cannot be None")
        if t is None:
            raise ValueError("Variable name cannot be None")
        vs = result.csvpath.variables
        if vs is None:
            raise ValueError("Variables cannot be None")
        if t not in vs:
            msg = f"Variable {t} not found in variables"
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            raise InputException(msg)
        #
        # get the target file name
        #
        f = vs[t]
        if f is None or str(f).strip() == "":
            msg = f"Variable {t} is invalid: {f}"
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            raise InputException(msg)
        #
        # if we're shipping to another backend, we don't need to change the target location
        #
        if not Nos(f).is_local:
            return f

        if f.find("..") != -1:
            msg = f"Transfer path cannot include '..': {f}"
            self.csvpaths.error_manager.handle_error(source=self, msg=msg)
            raise InputException(msg)
        p = result.csvpath.config.transfer_root
        rp = Nos(p).join(f)
        sep = Nos(rp).sep
        rd = rp[0 : rp.rfind(sep)]
        #
        # should this be dir_exists()?
        #
        if not Nos(rd).exists():
            Nos(rd).makedir()
        return rp

    def _path_to_result(self, result, t) -> str:
        if result is None:
            raise ValueError("Result cannot be None")
        if t is None:
            raise ValueError("Path to result file cannot be None")
        d = result.instance_dir
        o = Nos(d).join(t)
        sep = Nos(o).sep
        r = o[0 : o.rfind(sep)]
        if not Nos(r).exists():
            Nos(r).makedirs()
            Nos(r).makedir()
        return o
