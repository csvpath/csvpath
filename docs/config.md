
# Config

CsvPaths has a few config options. By default, the config options are in `./config/config.ini`. You can change the location of your .ini file in two ways:
- Set a `CSVPATH_CONFIG_FILE` env var pointing to your file
- Create an instance of CsvPathConfig, set its CONFIG property, and call the `reload()` method

The config options, at this time, are about:
- File extensions
- Error handling
- Logging

There are two types of files you can set extensions for:
- CSV files
- CsvPath files

## File Extensions

The defaults for these are:

```ini
    [csvpath_files]
    extensions = txt, csvpath

    [csv_files]
    extensions = txt, csv, tsv, dat, tab, psv, ssv
```

## Error Handling

The error settings are for when CsvPath or CsvPaths instances encounter problems. The options are:
- `stop` - Halt processing; the CsvPath stopped property is set to True
- `fail` - Mark the currently running CsvPath as having failed
- `raise` - Raise the exception in as noisy a way as possible
- `quiet` - Do nothing that affects the system out; this protects command line redirection of `print()` output. Logging is also minimized such that errors that would release a lot of metadata are slimmed down.
- `collect` - Collect the errors in the error results for the CsvPath. This option is available with and without a CsvPaths instance.

Multiple of these settings can be configured together. Quiet and raise do not coexist well. Raise will win because seeing problems lets you fix them.

## Logging

Logging levels are set at the major-component level. The components are:
- `csvpath`
- `csvpaths`
- `matcher`
- `scanner`

Four levels are available:
- `error`
- `warning`
- `debug`
- `info`

The levels are intended for the same functionality as their Python equivalents.

CsvPath logs are directed to a file. The log file settings are:
- `log_file` - a path to the log
- `log_files_to_keep` - a number of logs, 1 to 100, kept in rotation before being deleted
- `log_file_size` - an indication of roughly when a log file will be rotated

As an example:
```ini
    log_file = logs/csvpath.log
    log_files_to_keep = 100
    log_file_size = 52428800
```



