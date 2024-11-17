from csvpath import CsvPath, CsvPaths
import sys
import os
import time
from bullet import Bullet
from .drill_down import DrillDown


class Cli:
    def __init__(self):
        self._csvpaths = CsvPaths()

    def clear(self):
        print(chr(27) + "[2J")

    def loop(self):
        while True:
            self.clear()
            b = Bullet(
                bullet=" > ",
                choices=[
                    "named-files",
                    "named-paths",
                    "run",
                    "results",
                    "quit",
                ],
            )
            t = b.launch()
            if t == "quit":
                print(chr(27) + "[2J")
                return
            if t == "run":
                try:
                    self.clear()
                    self.run()
                except Exception as e:
                    print(f"Error: {e}")
                    self._input("Hit return to continue")
                continue
            if t == "named-files":
                self.clear()
                b = Bullet(
                    bullet=" > ",
                    choices=[
                        "add named-file",
                        "list named-files",
                    ],
                )
                t = b.launch()
                try:
                    if t == "add named-file":
                        DrillDown(self).name_file()
                    if t == "list named-files":
                        self.list_named_files()
                except Exception as e:
                    print(f"Error: {e}")
                    self._input("Hit return to continue")
                continue
            if t == "named-paths":
                self.clear()
                b = Bullet(
                    bullet=" > ",
                    choices=[
                        "add named-paths",
                        "list named-paths",
                    ],
                )
                t = b.launch()
                try:
                    if t == "add named-paths":
                        DrillDown(self).name_paths()
                    if t == "list named-paths":
                        self.list_named_paths()
                except Exception as e:
                    print(f"Error: {e}")
                    self._input("Hit return to continue")
                continue
            if t == "list archive":
                self.clear()
                pass
            if t == "list named-paths runs":
                self.clear()
                pass
            if t == "list named-paths run":
                self.clear()
                pass

    def _response(self, text: str) -> None:
        sys.stdout.write(f"\033[92m {text}\033[0m\n")

    def _input(self, prompt: str) -> str:
        try:
            response = input(f"{prompt}\033[93m")
            sys.stdout.write("\033[0m")
            return response.strip()
        except KeyboardInterrupt:
            return "quit"

    def list_named_paths(self):
        self.clear()
        names = self._csvpaths.paths_manager.named_paths_names
        names.sort()
        print(f"{len(names)} named-paths names:")
        for n in names:
            print(f"   {n}")
        self._input("hit return to continue")

    def list_named_files(self):
        self.clear()
        names = self._csvpaths.file_manager.named_file_names
        names.sort()
        print(f"{len(names)} named-file names:")
        for n in names:
            print(f"   {n}")
        self._input("hit return to continue")

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
        cli = Bullet(bullet=" > ", choices=["collect", "fast forward"])
        method = cli.launch()
        self.clear()
        sys.stdout.write(
            f"\033[36m Running {paths} against {file} using {method}\033[0m\n"
        )
        time.sleep(1.2)
        if method == "collect":
            self._csvpaths.collect_paths(filename=file, pathsname=paths)
        else:
            self._csvpaths.fast_forward_paths(filename=file, pathsname=paths)
        self._input("\nHit return to continue")


def run():
    cli = Cli()
    cli.loop()


if __name__ == "__main__":
    run()
