import sys
import os
import time
import traceback
from csvpath import CsvPaths
from .drill_down import DrillDown
from .select import Select
from .error import Error


class Cli:
    def __init__(self):
        self.csvpaths = CsvPaths()

    def clear(self):
        print(chr(27) + "[2J")

    def pause(self):
        time.sleep(1.2)

    def short_pause(self):
        time.sleep(0.5)

    ITALIC = "\033[3m"
    SIDEBAR_COLOR = "\033[36m"
    REVERT = "\033[0m"
    STOP_HERE = f"{SIDEBAR_COLOR}{ITALIC}... done picking dir{REVERT}"
    STOP_HERE2 = "👍 pick this dir"
    CANCEL = f"{SIDEBAR_COLOR}{ITALIC}... cancel{REVERT}"
    CANCEL2 = "← cancel"

    def _return_to_cont(self):
        print(
            f"\n{Cli.SIDEBAR_COLOR}{Cli.ITALIC}... Hit return to continue{Cli.REVERT}\n"
        )
        self._input("")

    def _response(self, text: str) -> None:
        sys.stdout.write(f"\u001b[30;1m{text}{Cli.REVERT}\n")

    def action(self, text: str) -> None:
        sys.stdout.write(f"\033[36m{text}{Cli.REVERT}\n")

    def _input(self, prompt: str) -> str:
        try:
            response = input(f"{prompt}\033[93m")
            sys.stdout.write(Cli.REVERT)
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
        if choices[len(choices) - 1] == Cli.CANCEL:
            choices[len(choices) - 1] = Cli.CANCEL2
        if choices[len(choices) - 2] == Cli.STOP_HERE:
            choices[len(choices) - 2] = Cli.STOP_HERE2
        cs = [(s, s) for s in choices]
        t = Select().ask(title="", values=cs, cancel_value="CANCEL")
        self.clear()
        return t

    def loop(self):
        while True:
            t = None
            try:
                choices = [
                    "named-files",
                    "named-paths",
                    "named-results",
                    "run",
                    "config",
                    "quit",
                ]
                t = self.ask(choices)
            except KeyboardInterrupt:
                self.end()
                return
            t = self._do(t)
            if t == "quit":
                self.end()
                return

    def _do(self, t: str) -> str | None:
        if t == "quit":
            return t
        try:
            if t == "run":
                self.run()
            if t == "named-files":
                self._files()
            if t == "named-paths":
                self._paths()
            if t == "named-results":
                self._results()
            if t == "config":
                self._config()
        except KeyboardInterrupt:
            return "quit"
        except Exception:
            print(traceback.format_exc())
            self._return_to_cont()

    def _config(self) -> None:
        Error(self).show()

    def _files(self) -> None:
        choices = ["add named-file", "list named-files", "cancel"]
        t = self.ask(choices)
        if t == "add named-file":
            DrillDown(self).name_file()
        if t == "list named-files":
            self.list_named_files()

    def _paths(self) -> None:
        choices = ["add named-paths", "list named-paths", "cancel"]
        t = self.ask(choices)
        if t == "add named-paths":
            DrillDown(self).name_paths()
        if t == "list named-paths":
            self.list_named_paths()

    def _results(self) -> None:
        choices = ["open named-result", "list named-results", "cancel"]
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
            names.append(self.CANCEL)
            t = self.ask(names)
            if t == self.CANCEL:
                return
            t = f"{self.csvpaths.config.archive_path}{os.sep}{t}"
            self.action(f"Opening results at {t}...")
            self.short_pause()
            c = f"open {t}"
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
        file = self.ask(files, q="What named-file? ")
        self.clear()
        allpaths = self.csvpaths.paths_manager.named_paths_names
        if len(allpaths) == 0:
            input("You must add a named-paths file. Press any key to continue.")
            return
        paths = self.ask(allpaths, q="What named-paths? ")
        self.clear()
        choices = ["collect", "fast-forward"]
        method = self.ask(choices, q="What method? ")
        self.clear()
        self.action(f"Running {paths} against {file} using {method}\n")
        self.pause()
        try:
            if method == "collect":
                self.csvpaths.collect_paths(filename=file, pathsname=paths)
            else:
                self.csvpaths.fast_forward_paths(filename=file, pathsname=paths)
        except Exception:
            cfg = None
            while cfg in [None, "c", "e"]:
                print("\nThere was an error.")
                print("Click 'e' and return to print the stack trace. ")
                print("Click 'c' and return to change config options. ")
                print("Click return to continue. ")
                cfg = input("")
                if cfg == "c":
                    Error(self).show()
                elif cfg == "e":
                    self.clear()
                    print(traceback.format_exc())
                    input("\n\nClick return to continue")
                else:
                    return
                self.clear()
        self._return_to_cont()


def run():
    cli = Cli()
    cli.loop()


if __name__ == "__main__":
    run()
