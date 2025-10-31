
<a name="settings"></a>
# Mode Settings

Metadata fields can be used to control several run modes. These include:
- `logic-mode` - Sets the CsvPath instance to operate in AND or OR mode
- `return-mode` - Instructs the CsvPath instance to return matches or lines that did not match
- `print-mode` - Determines if the printouts from `print()` go to the terminal's standard out, or not
- `validation-mode` - Sets the validation reporting actions and channels
- `run-mode` - Indicates if a csvpath should be run by its CsvPath instance
- `unmatched-mode` - Instructs CsvPath Framework to collect unmatched lines, or not
- `explain-mode` - If set, an explanation of the match results is dumped to INFO for each line processed

The values for each are:

- `logic-mode` == `OR` or `AND` (`AND` is the default)
- `return-mode` == `no-matches` or `matches` (`matches` is the default)
- `print-mode` == `no-default` or `default` (`default` is the default)
- `run-mode` == `no-run` or `run` (`run` is the default)
- `explain-mode` == `no-explain` or `explain` (`no-explain` is the default)
- `unmatched-mode` == `keep` or `no-keep` (`no-keep` is the default)
- `validation-mode` ==
    - `print` or `no-print` (`print` is on by default) and/or
    - `raise` or `no-raise` and/or
    - `log` (`log` can only be turned off programmatically)
    - `stop` or `no-stop`
    - `fail` or `no-fail`

For more modes and more details about each, see [csvpath.org](https://www.csvpath.org).

The metadata settings happen after the `parse()` method and before `collect()`, `fast_forward()`, or `next()` evaluates the file. If neither the positive (e.g. `print`) or the negative (e.g. `no-print`) is found the fallback is the setting in config.ini, if there is one, otherwise, the default.

Metadata driven settings are effective only for the csvpath they are declared in. When you are using a `CsvPaths` instance to manage a multi-`CsvPath` instance run these metadata fields give you a way to configure different behavior for each `CsvPath` in the run. Likewise, a production operator can configure a project-wide default setting in `config.ini`, while csvpath writers still have the option to override it on a csvpath-by-csvpath basis.


