import sys
import os
import time
import traceback
from csvpath import CsvPaths
from .drill_down import DrillDown
from .selecter import Selecter
from .debug_config import DebugConfig
from csvpath.util.nos import Nos
from .asker import Asker
from .function_lister import FunctionLister
from .const import Const


class Cli:
    def __init__(self):
        self.csvpaths = CsvPaths()
        self.clear()
        """
        splash = ""
          *** *            ******        **  **
        ***  **   *        **  **      **** **
       **        ** **  * ** *** ***** **  *****
       **    * **** **** ***** *** ** **  ** **
       **   **** ****** **     ** ** *** ** ** **
         ***   **** *  **      *** ** ****   **
***************************
CsvPath Command Line Interface
Try tab completion and menu-by-key.
For help see https://www.csvpath.org
"""
        print(Const.SPLASH)
        self._return_to_cont()
        self.clear()

    def clear(self):
        print(chr(27) + "[2J")

    def pause(self):
        time.sleep(1.2)

    def short_pause(self):
        time.sleep(0.5)

    ITALIC = "\033[3m"
    # SIDEBAR_COLOR = "\033[36m"
    # REVERT = "\033[0m"
    # STOP_HERE = f"{Const.SIDEBAR_COLOR}{ITALIC}... done picking dir{Const.REVERT}"
    # STOP_HERE2 = "👍 pick this dir"
    # CANCEL = f"{Const.SIDEBAR_COLOR}{ITALIC}... cancel{Const.REVERT}"
    # CANCEL2 = "← cancel"
    # QUIT = "← quit"
    # NAMED_FILES = "register data"
    # NAMED_PATHS = "load csvpaths"
    # ARCHIVE = "access the archive"

    def _return_to_cont(self):
        print(
            f"\n{Const.SIDEBAR_COLOR}{Cli.ITALIC}... Hit return to continue{Const.REVERT}\n"
        )
        self._input("")

    def _response(self, text: str) -> None:
        sys.stdout.write(f"\u001b[30;1m{text}{Const.REVERT}\n")

    def action(self, text: str) -> None:
        sys.stdout.write(f"\033[36m{text}{Const.REVERT}\n")

    def _input(self, prompt: str) -> str:
        try:
            response = input(f"{prompt}\033[93m")
            sys.stdout.write(Const.REVERT)
            return response.strip()
        except KeyboardInterrupt:
            return "cancel"

    def end(self) -> None:
        print(chr(27) + "[2J")

    def ask(self, choices: list[str], q=None) -> str:
        self.clear()
        if len(choices) == 0:
            return
        if q is not None:
            print(q)
        if choices[len(choices) - 1] == Const.CANCEL:
            choices[len(choices) - 1] = Const.CANCEL2
        if choices[len(choices) - 2] == Const.STOP_HERE:
            choices[len(choices) - 2] = Const.STOP_HERE2
        cs = [(s, s) for s in choices]
        t = Selecter().ask(title="", values=cs, cancel_value=Const.CANCEL)
        self.clear()
        return t

    def loop(self):
        while True:
            t = None
            try:
                choices = [
                    Const.NAMED_FILES,
                    Const.NAMED_PATHS,
                    Const.ARCHIVE,
                    "run",
                    "config",
                    "functions",
                    Const.QUIT,
                ]
                t = self.ask(choices)
            except KeyboardInterrupt:
                self.end()
                return
            t = self._do(t)
            if t == Const.QUIT:
                self.end()
                return

    def _do(self, t: str) -> str | None:
        if t == Const.QUIT:
            return t
        try:
            if t == "run":
                self.run()
            if t == Const.NAMED_FILES:
                self._files()
            if t == Const.NAMED_PATHS:
                self._paths()
            if t == Const.ARCHIVE:
                self._results()
            if t == "config":
                self._config()
            if t == "functions":
                self._functions()
        except KeyboardInterrupt:
            return Const.QUIT
        except Exception:
            print(traceback.format_exc())
            self._return_to_cont()

    def _functions(self) -> None:
        FunctionLister(self).list_functions()

    def _config(self) -> None:
        DebugConfig(self).show()

    def _files(self) -> None:
        choices = ["add named-file", "list named-files", Const.CANCEL2]
        t = self.ask(choices)
        if t == "add named-file":
            DrillDown(self).name_file()
        if t == "list named-files":
            self.list_named_files()

    def _paths(self) -> None:
        choices = ["add named-paths", "list named-paths", Const.CANCEL2]
        t = self.ask(choices)
        if t == "add named-paths":
            DrillDown(self).name_paths()
        if t == "list named-paths":
            self.list_named_paths()

    def _results(self) -> None:
        choices = ["open named-result", "list named-results", Const.CANCEL2]
        t = self.ask(choices)
        if t == "open named-result":
            self.open_named_result()
        if t == "list named-results":
            self.list_named_results()

    def list_named_results(self):
        self.clear()
        names = self.csvpaths.results_manager.list_named_results()
        print(f"{len(names)} named-results names:")
        for n in names:
            if n.find(".") > -1:
                continue
            self._response(f"   {n}")
        self._return_to_cont()

    def open_named_result(self):
        self.clear()
        try:
            names = self.csvpaths.results_manager.list_named_results()
            names = [n for n in names if n.find(".") == -1]
            print(f"{len(names)} named-results names:")
            names.append(Const.CANCEL)
            t = self.ask(names)
            if t == Const.CANCEL:
                return
            t = f"{self.csvpaths.config.archive_path}{os.sep}{t}"
            self.action(f"Opening results at {t}...")
            self.short_pause()
            #
            # not sure if this works for the linux desktop user
            #
            c = f"open {t}" if os.sep == "/" else f"explorer {t}"
            os.system(c)
        except Exception:
            print(traceback.format_exc())

    def list_named_paths(self):
        self.clear()
        names = self.csvpaths.paths_manager.named_paths_names
        names.sort()
        print(f"{len(names)} named-paths names:")
        for n in names:
            self._response(f"   {n}")
        self._return_to_cont()

    def list_named_files(self):
        self.clear()
        names = self.csvpaths.file_manager.named_file_names
        names.sort()
        print(f"{len(names)} named-file names:")
        for n in names:
            self._response(f"   {n}")
        self._return_to_cont()

    def run(self):
        self.clear()
        files = self.csvpaths.file_manager.named_file_names
        if len(files) == 0:
            input("You must add a named-file. Press any key to continue.")
            return
        files.sort()
        file = self.ask(
            files, q="What named-file? \n(enter $ on any line to build a reference) "
        )
        #
        # if '$' user wants to use a reference, possibly for replay
        #
        if file.startswith("$"):
            # find the run and instance
            file = self.complete_file_reference()
            if file is None:
                input(
                    "Could not build the reference. Check if all files are present. Press any key to continue."
                )
                return

        self.clear()
        allpaths = self.csvpaths.paths_manager.named_paths_names
        if len(allpaths) == 0:
            input("You must add a named-paths file. Press any key to continue.")
            return
        allpaths.sort()
        paths = self.ask(
            allpaths,
            q="What named-paths? \n(enter $ on any line to build a reference) ",
        )
        #
        # if '$' user wants to use a reference to rewind
        #
        if paths.startswith("$"):
            paths = self.complete_paths_reference(paths)

        self.clear()
        choices = ["collect", "fast-forward", Const.CANCEL2]
        method = self.ask(choices, q="What method? ")
        self.clear()
        if method == Const.CANCEL2:
            return
        self.action(f"Running {paths} against {file} using {method}\n")
        self.pause()
        try:
            if method == "collect":
                self.csvpaths.collect_paths(filename=file, pathsname=paths)
            else:
                self.csvpaths.fast_forward_paths(filename=file, pathsname=paths)
        except Exception as e:
            self.csvpaths.logger.error(e)
            cfg = None
            while cfg in [None, "c", "e"]:
                print("\nThere was an error.")
                print("Click 'e' and return to print the stack trace. ")
                print("Click 'c' and return to change config options. ")
                print("Click return to continue. ")
                cfg = input("")
                if cfg == "c":
                    DebugConfig(self).show()
                elif cfg == "e":
                    self.clear()
                    print(traceback.format_exc())
                    input("\n\nClick return to continue")
                else:
                    return
                self.clear()
        self._return_to_cont()

    def complete_file_reference(self) -> str:
        allpaths = self.csvpaths.paths_manager.named_paths_names
        allpaths.sort()
        file = self.ask(allpaths, q="Building a reference. Use what results? ")
        file = file.lstrip("$")
        results = self.csvpaths.config.get(section="results", name="archive")
        results = f"{results}{os.sep}{file}"
        if not Nos(results).dir_exists():
            return None
        runs = Nos(results).listdir()
        runs.sort()
        run = self.ask(runs, q="Which run? ")
        run = run.lstrip("$")
        results = f"{results}{os.sep}{run}"
        instances = Nos(results).listdir()
        instances = [i for i in instances if i.find(".json") == -1]
        instance = self.ask(instances, q="Which csvpath? ")
        instance = instance.lstrip("$")
        return f"${file}.results.{run}.{instance}"

    def complete_paths_reference(self, paths) -> str:
        allpaths = self.csvpaths.paths_manager.named_paths_names
        allpaths.sort()
        path = self.ask(allpaths, q="Building a reference. Use what paths? ")
        path = path.lstrip("$")
        instances = self.csvpaths.paths_manager.get_identified_paths_in(path)
        ids = [i[0] for i in instances]
        run = self.ask(ids, q="Which csvpath? ")
        run = run.lstrip("$")
        # ft = Asker(self, name_type="none").ask("from:, to:, or neither? ")
        ft = self.ask(
            ["from", "to", "neither"], q=f"Limit csvpaths in group relative to {run}? "
        )
        ft = ft.lstrip("$")
        ft = ft.replace(":", "")
        ft = ft.strip()
        if ft in ["from", "to"]:
            ft = f":{ft}"
        else:
            ft = ""
        return f"${path}.csvpaths.{run}{ft}"


def run():
    cli = Cli()
    cli.loop()


if __name__ == "__main__":
    run()
