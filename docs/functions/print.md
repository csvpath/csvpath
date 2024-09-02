
# Print

Prints to std.out and/or to a <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/util/printer.py'>Printer object</a>.

`print()` is helpful for debugging and validation. Print can also be a quick way to create an output .csv or in another way capture the data generated during a run.

Print takes a string argument and, optionally, a function. The function is executed after the printout.


## Variables

Print strings can include the following variables.

| Variable name     | Description                                                           |
|-------------------|-----------------------------------------------------------------------|
|name               | The name of the file. E.g. for `$file.csv[*][no()]` it is `file`.     |
|delimiter          | The file's delimiter                                                  |
|quotechar          | The quote character the file uses to quote columns                    |
|count_matches      | The current number of matches                                         |
|count_lines        | The current line being processed                                      |
|count_scans        | The current number of lines scanned                                   |
|headers            | The list of header values                                             |
|headers.headername | The value of the named header                                         |
|scan_part          | The scan pattern                                                      |
|match_part         | The match pattern                                                     |
|variables          | The value of variables                                                |
|variables.varname  | The value of the named variable                                       |
|match_json         | A JSON dump of the match part parse tree                              |
|line               | The list of values that is the current line being processed           |
|last_row_time      | Time taken for the last row processed                                 |
|rows_time          | Time taken for all rows processed so far                              |

A variable is indicated as a qualifier off the root. The root is `$`, so the `delimiter` variable is referred to like this:

    $.delimiter

## Examples

    "$.name's delimiter is $.delimiter."

    "The match part JSON was parsed into this tree:\n
        $.match_json"

