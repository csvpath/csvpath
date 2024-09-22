
# Print Line

`print_line()` gives you a way to output the current line, in whole or part, as-is. The function takes two optional arguments:
- The delimiter
- "quotes" or "single" to indicate all values should be quoted or single-quoted

As with all printing, the output goes to the Printer instances held by the CsvPath or Results. In the case of a CsvPaths managed run, the results go to the Results via the CsvPath, and will, by default, also be printed to standard out.

`print_line()` takes the `onmatch` qualifier.

## Examples

```bash
    $[1*][
        random(0, 1) == 1 -> print_line()
        print_queue() == 100 -> stop()
    ]
```

This path prints a 100-line random sample of the first few hundred lines of a file. Typically the print will go to standard out. It may also be captured by a Printer instance for post-run processing. The easiest way to set that up is to use a CsvPaths instance. With CsvPaths the print output of a run is automatically available in the results.


