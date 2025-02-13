import os
import traceback
from csvpath.matching.functions.function_factory import FunctionFactory


class FunctionLister:
    def list_functions(self, *, path, extensions, json=False, dir_only=False) -> str:
        """
        #moving to its own branch
        names = os.listdir(path)
        names = self._filter_hidden(names)
        if dir_only:
            names = self._filter_dirs_only(path, names)
        else:
            names = self._filter_extensions(path, names, extensions)
        names.sort()
        names = self._decorate(path, names, select_dir=dir_only)
        t = self._cli.ask(names)
        if t in [self._cli.STOP_HERE, self._cli.STOP_HERE2]:
            return (path, True)
        if t in [self._cli.CANCEL, self._cli.CANCEL2]:
            return (path, False)
        if t.startswith("📂 ") or t.startswith("📄 "):
            t = t[2:]
        return os.path.join(path, t)
        """
