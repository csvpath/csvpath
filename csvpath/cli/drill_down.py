import os
import traceback
from .debug_config import DebugConfig
from .asker import Asker
from .const import Const


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
        t = self._get_add_type()
        if t == Const.CANCEL2:
            return
        self._cli.clear()
        name = None
        if t == "file":
            name = Asker(self._cli, name_type="files").ask()
        #
        # get path
        #
        p = self._get_path(t, self._cli.csvpaths.config.csv_file_extensions)
        if p is False:
            return
        #
        # do the add
        #
        self._cli.clear()
        self._cli.action(f"Adding: {p}\n")
        self._cli.pause()
        try:
            if t == "file":
                self._cli.csvpaths.file_manager.add_named_file(name=name, path=p)
            elif t == "dir":
                self._cli.csvpaths.file_manager.add_named_files_from_dir(dirname=p)
            else:
                self._cli.csvpaths.file_manager.set_named_files_from_json(filename=p)
        except Exception:
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
                    self._cli.clear()
                    print(traceback.format_exc())
                    input("\n\nClick return to continue")
                else:
                    return
                self._cli.clear()

    # ============================
    # Paths
    # ============================

    def name_paths(self):
        t = self._get_add_type()
        if t == Const.CANCEL2:
            return
        #
        # get name
        #
        self._cli.clear()
        name = None
        if t == "file":
            name = Asker(self._cli, name_type="paths").ask()
        #
        # get path
        #
        exts = self._cli.csvpaths.config.csvpath_file_extensions
        p = self._get_path(t, exts)
        if p is False:
            return
        #
        # do the add
        #
        self._cli.clear()
        self._cli.action(f"Adding: {p}\n")
        self._cli.pause()
        try:
            if t == "file":
                self._cli.csvpaths.paths_manager.add_named_paths_from_file(
                    name=name, file_path=p
                )
            elif t == "dir":
                self._cli.csvpaths.paths_manager.add_named_paths_from_dir(
                    name=name, directory=p
                )
            else:
                self._cli.csvpaths.paths_manager.add_named_paths_from_json(file_path=p)
        except Exception as e:
            self._cli.csvpaths.logger.error(e)
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
                    self._cli.clear()
                    print(traceback.format_exc())
                    input("\n\nClick return to continue")
                else:
                    return
                self._cli.clear()

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
            self._cli.action(f"{p}\n")
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
        choices = ["dir", "file", "json", Const.CANCEL2]
        t = None
        t = self._cli.ask(choices)
        return t

    def _drill_down(self, *, path, extensions, json=False, dir_only=False) -> str:
        names = os.listdir(path)
        names = self._filter_hidden(names)
        if dir_only:
            names = self._filter_dirs_only(path, names)
        else:
            names = self._filter_extensions(path, names, extensions)
        names.sort()
        names = self._decorate(path, names, select_dir=dir_only)
        t = self._cli.ask(names)
        if t in [Const.STOP_HERE, Const.STOP_HERE2]:
            return (path, True)
        if t in [Const.CANCEL, Const.CANCEL2]:
            return (path, False)
        if t.startswith("📂 ") or t.startswith("📄 "):
            t = t[2:]
        return os.path.join(path, t)

    def _decorate(self, path, names, select_dir=False) -> list[str]:
        ns = []
        for n in names:
            if n in [Const.STOP_HERE, Const.STOP_HERE2]:
                pass
            elif os.path.isfile(os.path.join(path, n)):
                n = f"📄 {n}"
            else:
                n = f"📂 {n}"
            ns.append(n)
        if select_dir is True:
            ns.append(Const.STOP_HERE)
        ns.append(Const.CANCEL)
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
