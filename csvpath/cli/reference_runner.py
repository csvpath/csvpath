import json
import os
import re
from tabulate import tabulate
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_expression_3 import ReferenceExpression3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.reference_results_3 import ReferenceResults3
from .asker import Asker
from .selecter import Selecter
from .const import Const
from .error_menu_utility import ErrorMenuUtility as erut


class ReferenceRunner:
    #
    # interactive "run reference expressions" menu -- handles both a
    # plain single CsvPath Reference Language v3 string (FILES/
    # CSVPATHS/RESULTS, via ReferenceFinderFactory3.for_reference() +
    # .resolve()) and a compound UNION/INTERSECT/SUBTRACT expression
    # (ReferenceExpression3), added 2026-10-20 for issue #416. Earlier
    # scoped out on the assumption that the compound form needed a
    # real multi-line input UI Asker does not have -- wrong: David's
    # own worked example writes the operator as a keyword in the
    # middle of ONE line ("$a UNION $b"), which the existing
    # single-line input box already handles fine; see
    # _parse_expression()'s own docstring for the actual mechanism.
    #
    MAX_RECENT = 10
    HISTORY_FILE_NAME = "cli_reference_history.json"
    #
    # a standalone UNION/INTERSECT/SUBTRACT keyword, surrounded by
    # whitespace -- matches the compendium's and #416's own worked
    # examples exactly (uppercase only, deliberately -- a lowercase
    # match risks firing on a literal word inside some unrelated
    # construct).
    #
    _OPERATOR_PATTERN = re.compile(r"\s+(UNION|INTERSECT|SUBTRACT)\s+")

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
            prompt="Expression? ",
            initial_text=initial_text,
        ).ask()
        if not expr:
            return
        self._run(expr)

    def _parse_expression(self, text: str):
        """splits `text` into (left, op, right) for ReferenceExpression3
        when it contains a standalone UNION/INTERSECT/SUBTRACT keyword
        -- issue #416, e.g. '$food.files.:all().:first() UNION
        $food.csvpaths.:all().:index(0)'. Returns None when no keyword
        is present at all, meaning `text` is an ordinary plain
        reference (unchanged, existing behavior).

        Deliberately does not support nesting (a sub-expression on
        either side, e.g. two operators on one line) -- no worked
        example asks for it, and this flat, one-line syntax has no
        clean way to say which side a second operator belongs to; a
        second keyword raises instead of guessing."""
        matches = list(self._OPERATOR_PATTERN.finditer(text))
        if not matches:
            return None
        if len(matches) > 1:
            raise ReferenceException3(
                "Only one UNION/INTERSECT/SUBTRACT operator is supported "
                "per expression -- nested sub-expressions are not yet "
                "supported."
            )
        match = matches[0]
        left = text[: match.start()].strip()
        right = text[match.end() :].strip()
        if not left or not right:
            raise ReferenceException3(
                "A reference expression needs a reference on both sides "
                f"of {match.group(1)}."
            )
        return left, match.group(1).lower(), right

    def _run(self, expression: str) -> None:
        if not expression:
            raise ValueError("expression cannot be None or empty")
        self._cli.clear()
        self._cli.action(f"Running {expression}\n")
        try:
            parsed = self._parse_expression(expression)
            if parsed is not None:
                left, op, right = parsed
                finder = ReferenceExpression3(
                    left=left, op=op, right=right, csvpaths=self._cli.csvpaths
                )
            else:
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
        # 0-based, matching :index()'s own 0-based semantics -- a
        # 1-based row number next to 0-based :index() results (#411)
        # invited exactly the confusion it's there to avoid.
        headers = ["#", "path", "uuid", "data"]
        rows = [[i, r.path, r.uuid, r.data] for i, r in enumerate(results)]
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
            # #412 -- a read/write failure here used to be logged only
            # (easy to miss -- the log file, not the CLI session, is
            # where it lands), which is consistent with David seeing a
            # successful run silently fail to show up in "rerun
            # recent" with no visible error at all. Printed here too
            # now, so a failure is never silent in the CLI itself.
            self._cli.csvpaths.logger.error(e)
            print(f"\nCould not read recent-expression history: {e}\n")
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
            # see _load_history()'s own comment on #412.
            self._cli.csvpaths.logger.error(e)
            print(f"\nCould not save this expression to recent history: {e}\n")
