
# Config

CsvPaths has a few config options. By default, the config options are in `./config/config.ini`. You can change the location of your .ini file in two ways:
- Set a `CSVPATH_CONFIG_FILE` env var pointing to your file
- Create an instance of CsvPathConfig, set its CONFIG property, and call the `reload()` method

The config options, at this time, are about:
- File system locations
- File extensions
- Error handling
- Logging
- Event listeners
- Custom functions

## File System Locations

CsvPath stores files in three places:
- The data staging location
- The csvpath files location
- An archive or namespace of results

The first two are in the `[inputs]` section as `files` and `csvpaths`. The default location for data files and csvpath files is under the `./inputs` directory. Each has its own folder. You can move these two locations anywhere you like.

The archive is set in the `[results]` section as `archive`. By default it is a directory named `archive`. You can name the archive anything you like. Keep in mind that as well as simply storing files, the archive is also a namespacing tool. If you have many data partners or separate data operations you may want to have separate archives. If you do use separate archives and you are running OpenLineage events you will see your events namespaced by archive name. See below for configuring OpenLineage event listeners.

In addition, there are cache, config, and log file locations. They have sensible defaults but can be moved, if needed.

## File Extensions

There are two types of files you can set extensions for:
- CSV files
- CsvPath files

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
- `print` - Prints the errors using the Printer interface to whatever printers are available. By default this goes to standard out.

Multiple of these settings can be configured together.`quiet` and `raise` do not coexist well; likewise `quiet` and `print`. `raise` will win over `quiet` because seeing problems lets you fix them. `print` is most useful in getting simple inline error messages when `raise` is off.

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

## Listeners

CsvPath generates events that it converts to manifest files full of asset and runtime metadata. You can add OpenLineage listeners that will send results to an OpenLineage server like Marquez. In principle any OpenLineage API could receive CsvPath events, but only Marquez is tested and supported.

Be aware, OpenLineage events are currently handled in line, not out of band, asynchronously. That means there is a small performance hit. Typically this would not be noticeable, but in certain instances it could be a factor. For example, CsvPath's hundreds of unit tests run slower when OpenLineage events are fired. This small performance hit may be remediated in the future if it becomes an issue.

The settings are:
```ini
    [listeners]
    #uncomment for OpenLineage events to a Marquez server
    #file = from csvpath.managers.files.file_listener_ol import OpenLineageFileListener
    #paths = from csvpath.managers.paths.paths_listener_ol import OpenLineagePathsListener
    #result = from csvpath.managers.results.result_listener_ol import OpenLineageResultListener
    #results = from csvpath.managers.results.results_listener_ol import OpenLineageResultsListener

    [marquez]
    base_url = http://localhost:5000
```

## Custom Functions

<a href='https://github.com/csvpath/csvpath/blob/main/docs/functions/implementing_functions.md'>See this page for how to create and run custom functions</a>



