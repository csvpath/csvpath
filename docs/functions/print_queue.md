
# Print Queue

`print_queue()` returns the number of strings sent to the printers. Each CsvPath can hold any number of Printer instances. By default, an instance of the StdOutPrinter sends everything printed to the console.

When you run a CsvPaths your printing is included in your results. Results are named for the named-paths you run. By default, the named results include all the print strings made by your csvpaths in a list. Since the results are being forwarded through the CsvPath, the CsvPath's printers also process them. Because of that, your results, by default, will go to both standard out and to the CsvPathResult instance. Changing that behavior is straightforward, if needed.

## Examples

```bash
    $[1*][
        random(0, 1) == 1 -> print_line()
        print_queue() == 100 -> quit()
    ]
```

This path prints a 100-line random sample of the CSV file it is processing.

