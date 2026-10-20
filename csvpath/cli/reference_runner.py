import json
import os
from tabulate import tabulate
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.reference_results_3 import ReferenceResults3
from .asker import Asker
from .selecter import Selecter
from .const import Const
from .error_menu_utility import ErrorMenuUtility as erut


class ReferenceRunner:
    #
    # interactive "run reference expressions" menu -- v1 scope is plain
    # single CsvPath Reference Language v3 strings only (FILES/CSVPATHS/
    # RESULTS, via ReferenceFinderFactory3.for_reference() + .resolve()).
    # The compound UNION/INTERSECT/SUBTRACT expression language
    # (ReferenceExpression3) is deliberately out of scope here -- it
    # needs a real multi-line input UI that Asker does not have today.
    #
    MAX_RECENT = 10
    HISTORY_FILE_NAME = "cli_reference_history.json"

    def __init__(self, cli):
        self._cli = cli

    def menu(self) -> None:
        choices = ["rerun recent", "new expression", Const.CANCEL2]
        t = self._cli.ask(choices)
        if t == "rerun recent":
            self._rerun_recent()
        elif t == "new expression":
            self._edit_and_run("")

    def _rerun_recent(self) -> None:
        recent = self._load_history()
        self._cli.clear()
        if len(recent) == 0:
            input("No recent expressions yet. Press any key to continue.")
            return
        #
        # value/display pairs, same pattern as FunctionLister -- the
        # displayed text is numbered, but the value returned on
        # selection is the exact, unmodified expression string.
        #
        values = [(e, f"{i + 1}. {e}") for i, e in enumerate(recent)]
        values.append((Const.CANCEL2, Const.CANCEL2))
        t = Selecter().ask(title="", values=values, cancel_value=Const.CANCEL2)
        self._cli.clear()
        if t in (None, Const.CANCEL, Const.CANCEL2):
            return
        self._edit_and_run(t)

    def _edit_and_run(self, initial_text: str) -> None:
        self._cli.clear()
        expr = Asker(
            self._cli,
            name_type="none",
            prompt="Reference expression? ",
            initial_text=initial_text,
        ).ask()
        if not expr:
            return
        self._run(expr)

    def _run(self, expression: str) -> None:
        if not expression:
            raise ValueError("expression cannot be None or empty")
        self._cli.clear()
        self._cli.action(f"Running {expression}\n")
        try:
            finder = ReferenceFinderFactory3.for_reference(
                reference=expression, csvpaths=self._cli.csvpaths
            )
            results = finder.resolve()
            self._remember(expression)
            self._display(results)
        except KeyboardInterrupt:
            #
            # a slow resolve (e.g. :log() against a large log file) is
            # otherwise uninterruptible except by ctrl-c -- and since
            # Cli._do()'s own KeyboardInterrupt handler treats ANY
            # ctrl-c as "quit the whole CLI", an uncaught one here would
            # kill the entire session just to cancel one query. Catch
            # it here instead, so cancelling only returns to this menu.
            #
            print("\nCancelled.\n")
            return
        except Exception as e:
            if not erut.handle(self._cli, e):
                return
        input("\nHit return to continue. ")

    def _display(self, results: ReferenceResults3) -> None:
        if len(results) == 0:
            print("No results.\n")
            return
        headers = ["#", "path", "uuid", "data"]
        rows = [[i + 1, r.path, r.uuid, r.data] for i, r in enumerate(results)]
        print(tabulate(rows, headers=headers, tablefmt="simple_grid"))
        print("")

    # ============================
    # Recent-expression history
    # ============================

    def _history_path(self) -> str:
        #
        # the archive root (gitignored, e.g. tmp/local/archive) is
        # local runtime state, same as the results it already holds --
        # not config/, which is tracked.
        #
        archive_dir = self._cli.csvpaths.config.archive_path
        os.makedirs(archive_dir, exist_ok=True)
        return os.path.join(archive_dir, self.HISTORY_FILE_NAME)

    def _load_history(self) -> list:
        path = self._history_path()
        if not os.path.isfile(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                history = json.load(f)
            if not isinstance(history, list):
                return []
            return [h for h in history if isinstance(h, str)]
        except Exception as e:
            self._cli.csvpaths.logger.error(e)
            return []

    def _remember(self, expression: str) -> None:
        if not expression:
            raise ValueError("expression cannot be None or empty")
        history = self._load_history()
        history = [h for h in history if h != expression]
        history.insert(0, expression)
        history = history[: self.MAX_RECENT]
        try:
            with open(self._history_path(), "w", encoding="utf-8") as f:
                json.dump(history, f)
        except Exception as e:
            self._cli.csvpaths.logger.error(e)
