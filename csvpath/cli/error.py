from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit.shortcuts import checkboxlist_dialog


class Error:
    def __init__(self, holder):
        self._holder = holder
        if hasattr(holder, "_cli"):
            self._cli = self._holder._cli
        else:
            self._cli = holder
        self._paths = self._cli.csvpaths
        self._config = self._paths.config

    def show(self):
        log_loc = self._config.get(section="logging", name="log_file")
        cfg_loc = self._config.config_path

        raising = "suppress" if self.is_raising() else "raise"
        raising_msg = f"Change error policy to {raising} exceptions."

        debugging = "INFO" if self.is_debugging() else "DEBUG"
        debugging_msg = f"Set logging to {debugging}. (Your log file  is at {log_loc})."

        results = checkboxlist_dialog(
            title="Config Settings",
            text=f"These settings are in your config file at {cfg_loc}. Changing them may help you debug. \nNote that surpressing errors is effective only when running CsvPath expressions, not when loading files.\n",
            values=[
                ("flip_debug", debugging_msg),
                ("flip_raise", raising_msg),
            ],
        ).run()

        if results and "flip_raise" in results:
            if self.is_raising():
                self._config.add_to_config("errors", "csvpaths", "print")
                self._config.add_to_config("errors", "csvpath", "print")
            else:
                self._config.add_to_config("errors", "csvpaths", "print, raise")
                self._config.add_to_config("errors", "csvpath", "print, raise")

        if results and "flip_debug" in results:
            if self.is_debugging():
                self._config.add_to_config("logging", "csvpath", "info")
                self._config.add_to_config("logging", "csvpaths", "info")
            else:
                self._config.add_to_config("logging", "csvpath", "debug")
                self._config.add_to_config("logging", "csvpaths", "debug")
        if results:
            self._config.save_config()
            self._config.reload()
            self._cli.csvpaths._set_managers()

    def is_debugging(self) -> bool:
        psd = self._config.get(section="logging", name="csvpaths")
        pd = self._config.get(section="logging", name="csvpath")
        return psd is True and pd is True

    def is_raising(self) -> bool:
        policy = self._config.get(section="errors", name="csvpath")
        return self._paths.ecoms.do_i_raise() and "raise" in policy
