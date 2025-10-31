
<a name="settings"></a>
# Mode Settings

Metadata fields can be used to control certain run modes:
- `logic-mode` -- sets the CsvPath instance to operate in AND or OR mode
- `return-mode` -- instructs the CsvPath instance to return matches or lines that did not match
- `print-mode` -- determines if the printouts from `print()` go to the terminal's standard out, or not
- `validation-mode` -- sets the validation reporting actions and channels
- `run-mode` -- indicates if a csvpath should be run by its CsvPath instance
- `explain-mode` -- if set, an explanation of the match results is dumped to INFO for each line processed

The values for each are:

- `logic-mode` == `OR` or `AND` (`AND` is the default)
- `return-mode` == `no-matches` or `matches` (`matches` is the default)
- `print-mode` == `no-default` or `default` (`default` is the default)
- `run-mode` == `no-run` or `run` (`run` is the default)
- `explain-mode` == `no-explain` or `explain` (`no-explain` is the default)
- `validation-mode` ==
    - `print` or `no-print` (`print` is on by default) and/or
    - `raise` or `no-raise` and/or
    - `log` (`log` can only be turned off programmatically)
    - `stop` or `no-stop`
    - `fail` or `no-fail`

The metadata settings happen after the `parse()` method and before `collect()`, `fast_forward()`, or `next()` processes the file. If neither the positive (e.g. `print`) or the negative (e.g. `no-print`) is found the fallback is the setting in config.ini.

Metadata driven settings are effective only for the csvpath they are declared in. When you are using a `CsvPaths` instance to manage a multi-`CsvPath` instance run these metadata fields give you a way to configure different behavior for each `CsvPath` in the run.


