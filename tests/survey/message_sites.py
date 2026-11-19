"""Step 1 of the validation output survey (#779): every line that can
produce a validation message.

A message site is one of:
- handle_error: a call to ...error_manager.handle_error(source=.., msg=..)
- raise: a raise of an exception built with arguments, e.g.
  raise MatchException(msg)
- reraise: a bare raise, which passes on an exception from elsewhere

Each site is listed with its file, line, kind, exception type and the
message expression as written. The list is what step 5 measures harness
coverage against.

Run from the repo root:
    python tests/survey/message_sites.py [--out sites.json] [--all]

By default only the areas that produce validation output are listed:
csvpath/matching, csvpath/scanning, csvpath/modes, csvpath/csvpath.py and
csvpath/managers/errors. --all lists the whole package, tagged by area.
"""

import argparse
import ast
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, asdict

VALIDATION_AREAS = (
    "csvpath/matching/",
    "csvpath/scanning/",
    "csvpath/modes/",
    "csvpath/managers/errors/",
    "csvpath/csvpath.py",
)


@dataclass
class Site:
    file: str
    line: int
    kind: str
    exception: str
    message: str
    function: str
    area: str


def _area(path: str) -> str:
    parts = path.split("/")
    if len(parts) > 2 and parts[1] in ("matching", "managers"):
        return "/".join(parts[1:3])
    return parts[1] if len(parts) > 1 else path


def _src(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:  # unparse can fail on odd nodes; the site still counts
        return "?"


class _Finder(ast.NodeVisitor):
    def __init__(self, *, path: str) -> None:
        self.path = path
        self.sites: list[Site] = []
        self._func: list[str] = []
        self._class: list[str] = []

    def _where(self) -> str:
        c = self._class[-1] if self._class else ""
        f = self._func[-1] if self._func else ""
        return f"{c}.{f}" if c else f

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class.append(node.name)
        self.generic_visit(node)
        self._class.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._func.append(node.name)
        self.generic_visit(node)
        self._func.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr == "handle_error":
            msg = None
            for k in node.keywords:
                if k.arg == "msg":
                    msg = k.value
            if msg is None and len(node.args) > 1:
                msg = node.args[1]
            self._add(node=node, kind="handle_error", exception="", message=msg)
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        if node.exc is None:
            self._add(node=node, kind="reraise", exception="", message=None)
        elif isinstance(node.exc, ast.Call):
            ex = _src(node.exc.func)
            msg = node.exc.args[0] if node.exc.args else None
            self._add(node=node, kind="raise", exception=ex, message=msg)
        else:
            # raise e, raise exceptions[0]: passes on an existing exception
            self._add(node=node, kind="reraise", exception=_src(node.exc), message=None)
        self.generic_visit(node)

    def _add(self, *, node: ast.AST, kind: str, exception: str, message) -> None:
        self.sites.append(
            Site(
                file=self.path,
                line=node.lineno,
                kind=kind,
                exception=exception,
                message=_src(message),
                function=self._where(),
                area=_area(self.path),
            )
        )


def find_sites(*, root: str = "csvpath", every_area: bool = False) -> list[Site]:
    if not os.path.isdir(root):
        raise ValueError(f"No package directory at {root}; run from the repo root")
    sites = []
    for d, _, files in os.walk(root):
        if "__pycache__" in d:
            continue
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(d, name).replace(os.sep, "/")
            if not every_area and not path.startswith(VALIDATION_AREAS):
                continue
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
            finder = _Finder(path=path)
            finder.visit(tree)
            sites.extend(finder.sites)
    sites.sort(key=lambda s: (s.file, s.line))
    return sites


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write the sites as JSON to this file")
    ap.add_argument("--all", action="store_true", help="the whole package")
    a = ap.parse_args(argv)
    sites = find_sites(every_area=a.all)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump([asdict(s) for s in sites], fh, indent=1)
    print(f"{len(sites)} message sites")
    print("by kind:", dict(Counter(s.kind for s in sites)))
    print("by area:")
    for area, n in Counter(s.area for s in sites).most_common():
        print(f"  {n:5}  {area}")
    print("raised exception types:")
    for ex, n in Counter(s.exception for s in sites if s.kind == "raise").most_common():
        print(f"  {n:5}  {ex}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
