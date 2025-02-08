from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit.shortcuts import checkboxlist_dialog


class DebugConfig:
    def __init__(self, holder):
        self._holder = holder
        if hasattr(holder, "_cli"):
            self._cli = self._holder._cli
        else:
            self._cli = holder
        self._paths = self._cli.csvpaths
        self._config = self._paths.config

    def show(self):
        cfg_loc = self._config.config_path

        raising_msg = "Raise exceptions"
        stopping_msg = "Stop on errors"
        debugging_msg = "Set logging to DEBUG level"
        full_msg = "Print detailed errors"

        defaults = []
        if self.is_raising():
            defaults.append("flip_raise")
        if self.is_stopping():
            defaults.append("flip_stop")
        if self.is_debugging():
            defaults.append("flip_debug")
        if self.is_full():
            defaults.append("flip_full")

        results = checkboxlist_dialog(
            title="Config Settings",
            text=f"These settings are in your config file at {cfg_loc}. Changing them may help you debug. \nNote that surpressing errors is effective only when running CsvPath expressions, not when loading files.\n",
            values=[
                ("flip_debug", debugging_msg),
                ("flip_raise", raising_msg),
                ("flip_stop", stopping_msg),
                ("flip_full", full_msg),
            ],
            default_values=defaults,
        ).run()
        if results:
            self.reconfig(results)

    def reconfig(self, results):
        self.flip_policy(results)
        self.flip_debug(results)
        self.flip_full(results)
        if results:
            self._config.save_config()
            self._config.reload()
            self._cli.csvpaths._set_managers()

    def flip_debug(self, results):
        if "flip_debug" in results:
            self._config.add_to_config("logging", "csvpath", "debug")
            self._config.add_to_config("logging", "csvpaths", "debug")
        else:
            self._config.add_to_config("logging", "csvpath", "info")
            self._config.add_to_config("logging", "csvpaths", "info")

    def flip_full(self, results):
        if "flip_full" in results:
            self._config.add_to_config("errors", "use_format", "full")
        else:
            self._config.add_to_config("errors", "use_format", "bare")

    def flip_policy(self, results):
        policy = "print"
        if "flip_stop" in results:
            policy += ", stop"
        if "flip_raise" in results:
            policy += ", raise"
        self._config.add_to_config("errors", "csvpath", policy)
        self._config.add_to_config("errors", "csvpaths", policy)

    def is_full(self) -> bool:
        return self._paths.ecoms.do_i_print_expanded()

    def is_debugging(self) -> bool:
        psd = self._config.get(section="logging", name="csvpaths")
        pd = self._config.get(section="logging", name="csvpath")
        return psd == "debug" and pd == "debug"

    def is_raising(self) -> bool:
        policy = self._config.get(section="errors", name="csvpath")
        return self._paths.ecoms.do_i_raise() and "raise" in policy

    def is_stopping(self) -> bool:
        cp = "stop" in self._config.get(section="errors", name="csvpath")
        csp = "stop" in self._config.get(section="errors", name="csvpaths")
        return cp and csp
