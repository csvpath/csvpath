from csvpath import CsvPath, CsvPaths
import sys
import os
import time
from bullet import Bullet


def clear():
    print(chr(27) + "[2J")


class Repl:
    def __init__(self):
        self._csvpaths = CsvPaths()

    def take_input(self):
        while True:
            clear()
            cli = Bullet(
                bullet=" > ",
                choices=[
                    "add file",
                    "add paths",
                    "list files",
                    "list paths",
                    "run",
                    "quit",
                ],
            )
            t = cli.launch()
            try:
                if t == "run":
                    self.run()
                if t == "add file":
                    self.name_files()
                if t == "add paths":
                    self.name_paths()
                if t == "list paths":
                    self.list_named_paths()
                if t == "list files":
                    self.list_named_files()
                if t == "quit":
                    print(chr(27) + "[2J")
                    return
            except Exception as e:
                print(f"Error: {e}")
                self._input("Hit return to continue")

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
        clear()
        names = self._csvpaths.paths_manager.named_paths_names
        print("Named-paths names:")
        for n in names:
            print(f"   {n}")
        self._input("hit return to continue")

    def list_named_files(self):
        clear()
        names = self._csvpaths.file_manager.named_file_names
        print("Named-files names:")
        for n in names:
            print(f"   {n}")
        self._input("hit return to continue")

    def run(self):
        clear()
        print("What named-file? ")
        files = self._csvpaths.file_manager.named_file_names
        cli = Bullet(bullet=" > ", choices=files)
        file = cli.launch()
        clear()
        print("What named-paths? ")
        allpaths = self._csvpaths.paths_manager.named_paths_names
        cli = Bullet(bullet=" > ", choices=allpaths)
        paths = cli.launch()
        clear()
        print("What method? ")
        cli = Bullet(bullet=" > ", choices=["collect", "fast forward"])
        method = cli.launch()
        clear()
        sys.stdout.write(
            f"\033[36m Running {paths} against {file} using {method}\033[0m\n"
        )
        time.sleep(1.2)
        if method == "collect":
            self._csvpaths.collect_paths(filename=file, pathsname=paths)
        else:
            self._csvpaths.fast_forward_paths(filename=file, pathsname=paths)
        self._input("\nHit return to continue")

    def name_paths(self):
        name = self._input("Name? ")
        t = None
        cli = Bullet(bullet=" > ", choices=["dir", "file", "json"])
        t = cli.launch()
        if t == "dir":
            p = self._input("Path? ")
            self._csvpaths.paths_manager.add_named_paths(name=name, from_dir=p)
        else:
            p = self._input("Path? (type '.' to select) ")
            if p == ".":
                while not os.path.isfile(p):
                    p = self.drill_down_paths_files(
                        p, json=True if t == "json" else False
                    )
            clear()
            sys.stdout.write(f"Adding: \033[36m {p}\033[0m\n")
            time.sleep(1.2)
            if t == "file":
                self._csvpaths.paths_manager.add_named_paths(name=name, from_file=p)
            else:
                self._csvpaths.paths_manager.add_named_paths(name=name, from_json=p)

    def drill_down_paths_files(self, path, json=False) -> str:
        names = os.listdir(path)
        names = [
            n for n in names if not n[0] == "." and self.is_our_csvpath_file(n, json)
        ]
        names.sort()
        clear()
        sys.stdout.write(f"\033[36m {path}\033[0m\n")
        cli = Bullet(bullet=" > ", choices=names)
        t = cli.launch()
        return os.path.join(path, t)

    def is_our_csvpath_file(self, name, json=False) -> bool:
        i = name.rfind(".")
        if i == -1:
            return True
        ext = name[i + 1 :]
        return ext in self._csvpaths.config.csvpath_file_extensions or (
            json and ext == "json"
        )

    def name_files(self):
        name = self._input("Name to add? ")
        t = None
        cli = Bullet(bullet=" > ", choices=["dir", "file", "json"])
        t = cli.launch()
        if t == "dir":
            p = self._input("Path? ")
            self._csvpaths.file_manager.add_named_files_from_dir(dirname=p)
        else:
            p = self._input("Path? (type '.' to select) ")
            if p == ".":
                while not os.path.isfile(p):
                    p = self.drill_down_data_files(
                        p, json=True if t == "json" else False
                    )
            clear()
            sys.stdout.write(f"Adding: \033[36m {p}\033[0m\n")
            time.sleep(1.2)
            if t == "file":
                self._csvpaths.file_manager.add_named_file(name=name, path=p)
            else:
                self._csvpaths.file_manager.set_named_files_from_json(
                    name=name, filename=p
                )

    def drill_down_data_files(self, path, json=False) -> str:
        names = os.listdir(path)
        names = [n for n in names if not n[0] == "." and self.is_our_data_file(n, json)]
        names.sort()
        clear()
        sys.stdout.write(f"\033[36m {path}\033[0m\n")
        cli = Bullet(bullet=" > ", choices=names)
        t = cli.launch()
        return os.path.join(path, t)

    def is_our_data_file(self, name, json=False) -> bool:
        i = name.rfind(".")
        if i == -1:
            return True
        ext = name[i + 1 :]
        return ext in self._csvpaths.config.csv_file_extensions or (
            json and ext == "json"
        )


if __name__ == "__main__":
    repl = Repl()
    repl.take_input()
