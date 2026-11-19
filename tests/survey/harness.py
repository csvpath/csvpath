"""Step 2 of the validation output survey (#779): run bad inputs through
every function and record what the user would see.

The seeds are the minimal valid calls in
tests/csvpath/functions/test_csvpath_functions_alias_smoke.py (CALLS).
For each seed the harness finds the function's own call in the text and
makes variants:

- each argument replaced by each value in BAD_VALUES;
- the last argument dropped, an extra argument added, no arguments;

and runs every variant in each placement (PLACEMENTS) and under each
error policy (POLICIES). Each run records what was printed, what was
collected, the exception raised, and how many lines matched. The output
is JSON lines, one run per line; detectors.py reads it.

Run from the repo root, with cloud providers off:
    python tests/survey/harness.py --out runs.jsonl [--only add,gt] [--jobs 4]

Network connections are blocked in each worker. Each run has a time
limit. Nothing here calls Jev or any remote service: the Jev family is
skipped, as in the smoke test.
"""

import argparse
import contextlib
import importlib.util
import io
import json
import os
import re
import signal
import socket
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool

import psutil

SMOKE = "tests/csvpath/functions/test_csvpath_functions_alias_smoke.py"
PATH = "tests/csvpath/test_resources/test.csv"
SCAN = "1-2"
RUN_SECONDS = 5
# a worker over this is killed by the watchdog; its run is a finding
WORKER_MAX_RSS = 1_500_000_000
BATCH = 100

#
# what a user might wrongly pass. each is a csvpath fragment. "@stk" is a
# stack: the prelude pushes one value onto it.
#
BAD_VALUES = {
    "none": "none()",
    "blank": '""',
    "word": '"abc"',
    "comma_number": '"1,000"',
    "negative": "-1",
    "zero": "0",
    "decimal": "2.5",
    # big as a count or index. not bigger: as a format() width,
    # 99999999999 makes Python build a ~100GB string (a finding, #779)
    "big": "999999",
    "unknown_header": "#nosuchheader",
    "string_header": "#lastname",
    "unknown_variable": "@nosuchvar",
    "stack": "@stk",
    "bool_function": "yes()",
    "string_function": "upper(#firstname)",
    "comparison": '"x" == "x"',
}
PRELUDE = 'push("stk", "a")'

PLACEMENTS = {
    "as_is": "{call}",
    "assigned": "@survey_v = {call}",
    "in_not": "not({call})",
    "in_or": "or({call}, no())",
}

POLICIES = ["collect, print", "raise, collect, print", "print"]

SKIP = {
    # remote model service
    "jev",
    "noul",
    "choice",
    "score",
    "criteria",
    # need a CsvPaths run
    "import",
    "jinja",
}


def load_seeds() -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("alias_smoke", SMOKE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {n: c for n, c in mod.CALLS.items() if n not in SKIP}


def find_call(*, text: str, name: str) -> tuple[int, int, int] | None:
    """start of the name, index of its "(", index of its matching ")" """
    m = re.search(rf"(?<![\w.#@$]){re.escape(name)}(\.\w+)*\(", text)
    if m is None:
        return None
    open_at = m.end() - 1
    depth = 0
    quote = None
    for i in range(open_at, len(text)):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return m.start(), open_at, i
    return None


def split_args(inner: str) -> list[str]:
    args, depth, quote, cur = [], 0, None, ""
    for ch in inner:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            args.append(cur.strip())
            cur = ""
            continue
        cur += ch
    if cur.strip():
        args.append(cur.strip())
    return args


def variants(*, name: str, seed: str) -> list[dict]:
    """each variant is the seed with the function's own call changed"""
    found = find_call(text=seed, name=name)
    out = [{"variant": "seed", "fragment": seed}]
    if found is None:
        return out
    start, open_at, close_at = found
    head = seed[start:open_at]
    args = split_args(seed[open_at + 1 : close_at])

    def rebuild(new_args: list[str]) -> str:
        return seed[:start] + f"{head}({', '.join(new_args)})" + seed[close_at + 1 :]

    for i in range(len(args)):
        for label, bad in BAD_VALUES.items():
            a = list(args)
            a[i] = bad
            out.append({"variant": f"arg{i}:{label}", "fragment": rebuild(a)})
    if args:
        out.append({"variant": "drop_last", "fragment": rebuild(args[:-1])})
    out.append({"variant": "extra_arg", "fragment": rebuild(args + ['"extra"'])})
    if args:
        out.append({"variant": "no_args", "fragment": rebuild([])})
    return out


def placed(*, name: str, fragment: str, placement: str) -> str | None:
    """put the function's call in a placement; None if it cannot be"""
    if placement == "as_is":
        return fragment
    found = find_call(text=fragment, name=name)
    if found is None:
        return None
    start, _, close_at = found
    call = fragment[start : close_at + 1]
    # only place a call that is a whole match component, not one inside
    # another function: that one is already placed by its seed
    if fragment[:start].count("(") != fragment[:start].count(")"):
        return None
    wrapped = PLACEMENTS[placement].format(call=call)
    return fragment[:start] + wrapped + fragment[close_at + 1 :]


class _Timeout(BaseException):
    # BaseException, so csvpath's "except Exception" cannot swallow it
    pass


def _alarm(signum, frame):
    raise _Timeout()


def _no_network(self, *args, **kwargs):
    raise OSError("survey harness: network is blocked")


def _init_worker() -> None:
    socket.socket.connect = _no_network
    socket.socket.connect_ex = _no_network
    signal.signal(signal.SIGALRM, _alarm)


def run_one(job: dict) -> dict:
    from csvpath import CsvPath
    from csvpath.util.printer import TestPrinter

    csvpath = f"${PATH}[{SCAN}][ {PRELUDE} {job['csvpath_body']} ]"
    rec = dict(job)
    rec["csvpath"] = csvpath
    printed = []
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", job["policy"])
    path.set_printers([TestPrinter()])
    path.print = lambda msg, *a, **k: printed.append(f"{msg}")
    exc = None
    lines = None
    started = time.perf_counter()
    out = io.StringIO()
    signal.alarm(RUN_SECONDS)
    try:
        # some messages go straight to stdout, e.g. "Parsing problem: ..."
        with contextlib.redirect_stdout(out):
            path.parse(csvpath)
            lines = len(path.collect())
    except _Timeout:
        exc = ("Timeout", "")
    except (Exception, SystemExit) as e:  # the type and message are recorded
        exc = (type(e).__name__, f"{e}")
    finally:
        signal.alarm(0)
    rec["seconds"] = round(time.perf_counter() - started, 4)
    rec["printed"] = printed
    rec["stdout"] = out.getvalue()[:2000]
    rec["errors"] = [
        {
            "source": f"{e.source}",
            "message": f"{e.message}",
            "line": getattr(e, "line_count", None),
        }
        for e in (path.errors or [])
    ]
    v = (path.variables or {}).get("survey_v", "<unset>")
    rec["value"] = v if isinstance(v, (str, int, float, bool, type(None))) else repr(v)
    rec["exception"] = exc
    rec["lines"] = lines
    return rec


def jobs(*, only: set[str] | None) -> list[dict]:
    out = []
    for name, seed in sorted(load_seeds().items()):
        if only and name not in only:
            continue
        for v in variants(name=name, seed=seed):
            for placement in PLACEMENTS:
                body = placed(name=name, fragment=v["fragment"], placement=placement)
                if body is None:
                    continue
                for policy in POLICIES:
                    out.append(
                        {
                            "name": name,
                            "variant": v["variant"],
                            "placement": placement,
                            "policy": policy,
                            "csvpath_body": body,
                        }
                    )
    return out


def run_batch(batch: list[dict]) -> list[dict]:
    return [run_one(j) for j in batch]


class _Watchdog(threading.Thread):
    """kills a worker that grows past WORKER_MAX_RSS"""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.stop = False
        self.killed = 0

    def run(self) -> None:
        me = psutil.Process()
        while not self.stop:
            for c in me.children(recursive=True):
                try:
                    if c.memory_info().rss > WORKER_MAX_RSS:
                        c.kill()
                        self.killed += 1
                except psutil.Error:
                    pass
            time.sleep(0.25)


def _died(job: dict, why: str) -> dict:
    rec = dict(job)
    rec.update(
        csvpath=f"${PATH}[{SCAN}][ {PRELUDE} {job['csvpath_body']} ]",
        printed=[],
        stdout="",
        value="<unset>",
        errors=[],
        exception=("WorkerDied", why),
        lines=None,
        seconds=None,
    )
    return rec


def _run_pool(*, batches: list[list[dict]], n: int, write) -> list[list[dict]]:
    """runs the batches; returns the batches lost to a dead worker"""
    lost = []
    with ProcessPoolExecutor(n, initializer=_init_worker) as ex:
        futures = {ex.submit(run_batch, b): b for b in batches}
        for f in as_completed(futures):
            try:
                for rec in f.result():
                    write(rec)
            except BrokenProcessPool:
                lost.append(futures[f])
    return lost


def run_all(*, js: list[dict], n: int, write) -> None:
    dog = _Watchdog()
    dog.start()
    batches = [js[i : i + BATCH] for i in range(0, len(js), BATCH)]
    lost = _run_pool(batches=batches, n=n, write=write)
    #
    # a dead worker breaks the whole pool, so every unfinished batch comes
    # back. rerun them, then rerun what is still lost one job per pool to
    # find the job that kills its worker.
    #
    if lost:
        print(f"  {len(lost)} batches lost to a dead worker; rerunning", flush=True)
        lost = _run_pool(batches=lost, n=n, write=write)
    for b in lost:
        for j in b:
            again = _run_pool(batches=[[j]], n=1, write=write)
            if again:
                write(_died(j, "worker killed or crashed"))
    dog.stop = True
    print(f"  watchdog killed {dog.killed} workers")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", help="comma-separated function names")
    # 2 by default: David's VM runs hot with more
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--dry", action="store_true", help="count runs only")
    a = ap.parse_args(argv)
    only = set(a.only.split(",")) if a.only else None
    js = jobs(only=only)
    print(f"{len(js)} runs, {len({j['name'] for j in js})} functions")
    if a.dry:
        return 0
    started = time.perf_counter()
    count = [0]
    with open(a.out, "w", encoding="utf-8") as fh:

        def write(rec: dict) -> None:
            fh.write(json.dumps(rec) + "\n")
            count[0] += 1
            if count[0] % 5000 == 0:
                print(f"  {count[0]} runs, {time.perf_counter() - started:.0f}s", flush=True)

        run_all(js=js, n=a.jobs, write=write)
    print(f"{count[0]} runs done in {time.perf_counter() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
