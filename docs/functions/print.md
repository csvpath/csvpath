
# Print and Error

`print()` sends text to the console and/or to other <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/util/printer.py'>Printer object</a>.

`print()` is helpful for debugging and validation. It can also be a quick way to create an output CSV file or in another way capture the data generated during a run.

Print takes two arguments:
- A string to print
- Either a:
    - Function to execute (call matches()) after the printout happens
    - An Equality to execute after the printout happens
    - A Term that indicates a print stream/file/label separating one type of printing from another (note that at this time, while a `Printer` may support printing to files or other writables, the `print()` does not have a way to spin up a file to hand to the printer).

You can retrieve individual printout sets from `Result` objects like this:

```python
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/test_resources/named_files")
        paths.paths_manager.add_named_paths(
            name="print_test",
            paths=["""$[3][
                        print("my msg", "error")
                        print("my other msg", "foo-bar")
                   ]"""]
        )
        paths.fast_forward_paths(pathsname="print_test", filename="food")
        results = paths.results_manager.get_named_results("print_test")
        printout:list = results[0].get_printout_by_name("error")
        printout:list = results[0].get_printout_by_name("foo-bar")
```

## Variables

You can reference any of your own variables using a reference to the `variables` namespace. A variable named @cat would be referenced as:

```
    $.variables.cat
```

As well as user-defined variables, `print()` accepts csvpath runtime data and header values.

Headers are accessed in the same way as variables, but using the `headers` namespace. You may use indexes or names. If you need to quote a header name use single-quotes.

The built-in runtime values are as follows. You can reference them in the `csvpath` namespace.

| Variable name     | Description                                                           |
|-------------------|-----------------------------------------------------------------------|
| count_lines       | The total lines up to that point                                      |
| count_matches     | The matches seen to that point                                        |
| count_scans       | The lines scanned                                                     |
| delimiter         | The delimiter, most often a comma                                     |
| file_name         | The name of the file being processed                                  |
| headers           | The headers that are currently in-effect                              |
| identity          | The ID or name set in metadata to identify the csvpath being run      |
| last_line_time    | The number of milliseconds the last line took                         |
| line_number       | The currently processing line                                         |
| lines_collected   | The number of matched or unmatched lines collected                    |
| lines_time        | Cumulative processing time                                          |
| match_part        | The part of a csvpath that includes all the match components          |
| quotechar         | The character used to create a single from strings with spaces        |
| scan_part         | The first part of a csvpath that tells what file and lines to scan    |
| total_lines       | The total lines in the file                                           |
| valid             | True if the file is valid to that point                               |
|-------------------|-----------------------------------------------------------------------|
| explain-mode      | Prints the setting value                                              |
| logic-mode        | Prints the setting value                                              |
| print-mode        | Prints the setting value                                              |
| return-mode       | Prints the setting value                                              |
| run-mode          | Prints the setting value                                              |
| source-mode       | Prints the setting value                                              |
| unmatched-mode    | Prints the setting value                                              |
| validation-mode   | Prints the setting value                                              |

Again, a runtime value is indicated as a reference to the `csvpath` namespace. The root is `$`, so the `delimiter` variable is referred to like this:
```
    $.csvpath.delimiter
```

## Error

`error()` is very similar to `print()`. It sends its output to a printer and can run a match or equality in the same way. The differences are:
- `error()` wraps your text with the standard error metadata, if you configure your error messages to be decorated with IDs and a timestamp.
- The text you send using `error()` is logged and alerted with other errors and ends up in the `errors.json` file with all collected errors.


## Examples

    print("$.csvpath.identity's delimiter is $.csvpath.delimiter.")

    print("The file has $.csvpath.total_lines. There are two headers: $.headers.firstname, $headers.lastname")

