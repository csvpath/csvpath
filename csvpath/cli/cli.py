import sys
import os
import time
import traceback
from bullet import Bullet
from csvpath import CsvPath, CsvPaths
from .drill_down import DrillDown


class Cli:
    def __init__(self):
        self._csvpaths = CsvPaths()

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
    CANCEL = f"{SIDEBAR_COLOR}{ITALIC}... cancel{REVERT}"

    def _return_to_cont(self):
        print(
            f"\n{Cli.SIDEBAR_COLOR}{Cli.ITALIC}... Hit return to continue{Cli.REVERT}\n"
        )
        self._input("")

    def _response(self, text: str) -> None:
        sys.stdout.write(f"\u001b[30;1m{text}{Cli.REVERT}\n")

    def _action(self, text: str) -> None:
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

    def ask(self, choices: list[str]) -> str:
        self.clear()
        b = Bullet(bullet=" > ", choices=choices)
        t = b.launch()
        return t

    def loop(self):
        while True:
            t = None
            try:
                self.clear()
                b = Bullet(
                    bullet=" > ",
                    choices=[
                        "named-files",
                        "named-paths",
                        "named-results",
                        "run",
                        "quit",
                    ],
                )
                t = b.launch()
            except KeyboardInterrupt:
                self.end()
                return
            t = self._do(t)
            if t == "quit":
                self.end()
                return

    def _do(self, t: str) -> str | None:
        try:
            if t == "quit":
                return t
            if t == "run":
                self.run()
            if t == "named-files":
                self._files()
            if t == "named-paths":
                self._paths()
            if t == "named-results":
                self._results()
        except KeyboardInterrupt:
            return "quit"
        except Exception:
            print(traceback.format_exc())
            self._return_to_cont()

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
        if t == "cancel":
            return

    def _results(self) -> None:
        choices = ["open named-result", "list named-results", "cancel"]
        t = self.ask(choices)
        if t == "open named-result":
            self.open_named_result()
        if t == "list named-results":
            self.list_named_results()

    def list_named_results(self):
        self.clear()
        names = self._csvpaths.results_manager.list_named_results()
        print(f"{len(names)} named-results names:")
        for n in names:
            self._response(f"   {n}")
        self._return_to_cont()

    def open_named_result(self):
        self.clear()
        try:
            names = self._csvpaths.results_manager.list_named_results()
            print(f"{len(names)} named-results names:")
            names.append(self.CANCEL)
            cli = Bullet(bullet=" > ", choices=names)
            t = cli.launch()
            if t == self.CANCEL:
                return
            t = f"{self._csvpaths.config.archive_path}{os.sep}{t}"
            self._action(f"Opening results at {t}...")
            self.short_pause()
            c = f"open {t}"
            os.system(c)
        except Exception:
            print(traceback.format_exc())

    def list_named_paths(self):
        self.clear()
        names = self._csvpaths.paths_manager.named_paths_names
        names.sort()
        print(f"{len(names)} named-paths names:")
        for n in names:
            self._response(f"   {n}")
        self._return_to_cont()

    def list_named_files(self):
        self.clear()
        names = self._csvpaths.file_manager.named_file_names
        names.sort()
        print(f"{len(names)} named-file names:")
        for n in names:
            self._response(f"   {n}")
        self._return_to_cont()

    def run(self):
        self.clear()
        print("What named-file? ")
        files = self._csvpaths.file_manager.named_file_names
        cli = Bullet(bullet=" > ", choices=files)
        file = cli.launch()
        self.clear()
        print("What named-paths? ")
        allpaths = self._csvpaths.paths_manager.named_paths_names
        cli = Bullet(bullet=" > ", choices=allpaths)
        paths = cli.launch()
        self.clear()
        print("What method? ")
        cli = Bullet(bullet=" > ", choices=["collect", "fast-forward"])
        method = cli.launch()
        self.clear()
        self._action(f"Running {paths} against {file} using {method}\n")
        self.pause()
        try:
            if method == "collect":
                self._csvpaths.collect_paths(filename=file, pathsname=paths)
            else:
                self._csvpaths.fast_forward_paths(filename=file, pathsname=paths)
        except Exception:
            print(traceback.format_exc())
        self._return_to_cont()


def run():
    cli = Cli()
    cli.loop()


if __name__ == "__main__":
    run()
