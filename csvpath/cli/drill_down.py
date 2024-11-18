from csvpath import CsvPath, CsvPaths
import sys
import os
from bullet import Bullet


class DrillDown:
    def __init__(self, cli):
        self._cli = cli

    # ============================
    # File
    # ============================

    def name_file(self):
        #
        # get name
        #
        self._cli.clear()
        name = self._cli._input("Named-file name? ")
        #
        # get path
        #
        t = self._get_add_type()
        p = self._get_path(t, self._cli._csvpaths.config.csv_file_extensions)
        if p is False:
            return
        #
        # do the add
        #
        self._cli.clear()
        self._cli._action(f"Adding: {p}\n")
        self._cli.pause()
        if t == "file":
            self._cli._csvpaths.file_manager.add_named_file(name=name, path=p)
        elif t == "dir":
            self._cli._csvpaths.file_manager.add_named_files_from_dir(dirname=p)
        else:
            self._cli._csvpaths.file_manager.set_named_files_from_json(
                name=name, filename=p
            )

    # ============================
    # Paths
    # ============================

    def name_paths(self):
        #
        # get name
        #
        self._cli.clear()
        name = self._cli._input("Named-paths name? ")
        #
        # get path
        #
        t = self._get_add_type()
        exts = self._cli._csvpaths.config.csvpath_file_extensions
        p = self._get_path(t, exts)
        if p is False:
            return
        #
        # do the add
        #
        self._cli.clear()
        self._cli._action(f"Adding: {p}\n")
        self._cli.pause()
        if t == "file":
            self._cli._csvpaths.paths_manager.add_named_paths(name=name, from_file=p)
        elif t == "dir":
            self._cli._csvpaths.paths_manager.add_named_paths(name=name, from_dir=p)
        else:
            self._cli._csvpaths.paths_manager.add_named_paths(name=name, from_json=p)

    # ============================
    # Utilities
    # ============================

    def _get_path(self, t: str, extensions: list[str]) -> str:
        dir_only = t == "dir"
        p = "."
        if t == "json":
            extensions.append("")
            extensions.append("json")
        elif t == "file":
            extensions.append("")
        while p is not None and p != "" and not os.path.isfile(p):
            self._cli.clear()
            self._cli._action(f"{p}\n")
            p = self._drill_down(
                path=p,
                json=True if t == "json" else False,
                extensions=extensions,
                dir_only=dir_only,
            )
            if isinstance(p, tuple) and p[1] is True:
                p = p[0]
                break
            if isinstance(p, tuple) and p[1] is False:
                p = False
                break
        return p

    def _get_add_type(self) -> str:
        self._cli.clear()
        t = None
        cli = Bullet(bullet=" > ", choices=["dir", "file", "json"])
        t = cli.launch()
        return t

    def _drill_down(self, *, path, extensions, json=False, dir_only=False) -> str:
        names = os.listdir(path)
        names = self._filter_hidden(names)
        if dir_only:
            names = self._filter_dirs_only(path, names)
            names.sort()
        else:
            names = self._filter_extensions(path, names, extensions)
            names.sort()
        names = self._decorate(path, names, select_dir=dir_only)
        cli = Bullet(bullet=" > ", choices=names)
        t = cli.launch()
        if t == self._cli.STOP_HERE:
            return (path, True)
        if t == self._cli.CANCEL:
            return (path, False)
        if t.startswith("📂 ") or t.startswith("📄 "):
            t = t[2:]
        return os.path.join(path, t)

    def _decorate(self, path, names, select_dir=False) -> list[str]:
        ns = []
        for n in names:
            if n == self._cli.STOP_HERE:
                pass
            elif os.path.isfile(os.path.join(path, n)):
                n = f"📄 {n}"
            else:
                n = f"📂 {n}"
            ns.append(n)
        if select_dir is True:
            ns.append(self._cli.STOP_HERE)
        ns.append(self._cli.CANCEL)
        return ns

    def _filter_hidden(self, names) -> list[str]:
        if len(names) == 0:
            return []
        names = [n for n in names if not n[0] == "."]
        return names

    def _filter_files_only(self, path, names) -> list[str]:
        if len(names) == 0:
            return []
        ns = []
        for n in names:
            if os.path.isfile(os.path.join(path, n)):
                ns.append(n)
        return ns

    def _filter_dirs_only(self, path, names) -> list[str]:
        if len(names) == 0:
            return []
        ns = []
        for n in names:
            if not os.path.isfile(os.path.join(path, n)):
                ns.append(n)
        return ns

    def _filter_extensions(self, path, names, extensions) -> list[str]:
        if len(names) == 0:
            return []
        if len(extensions) == 0:
            return []
        ns = []
        for n in names:
            ext = self._ext_if(n)
            if ext in extensions:
                ns.append(n)
        return ns

    def _ext_if(self, name) -> str:
        i = name.rfind(".")
        if i == -1:
            return ""
        ext = name[i + 1 :]
        return ext
