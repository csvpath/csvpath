import traceback
from .debug_config import DebugConfig


class ErrorMenuUtility:
    @staticmethod
    def handle(cli, exception: Exception) -> bool:
        """
        Logs exception and shows the interactive CLI's standard
        after-exception menu: view the stack trace, open debug config,
        or continue. Returns False when the caller should return
        immediately (the user chose to continue without picking 'e' or
        'c'); True is never actually reached -- picking 'e' or 'c'
        always loops back into the same menu.
        """
        if cli is None:
            raise ValueError("cli cannot be None")
        if exception is None:
            raise ValueError("exception cannot be None")
        cli.csvpaths.logger.error(exception)
        cfg = None
        while cfg in [None, "c", "e"]:
            print("\nThere was an error.")
            print("Click 'e' and return to print the stack trace. ")
            print("Click 'c' and return to change config options. ")
            print("Click return to continue. ")
            cfg = input("")
            if cfg == "c":
                DebugConfig(cli).show()
            elif cfg == "e":
                cli.clear()
                print(traceback.format_exc())
                input("\n\nClick return to continue")
            else:
                return False
            cli.clear()
        return True
