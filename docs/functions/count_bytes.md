
# Count Bytes

When you run a named-paths group in a `CsvPaths` instance you can collect matching lines to each csvpath's results directory. You do this by running the `collect_paths()` or `collect_by_line()` methods, as well as any configuration settings needed for your purposes.

`count_bytes()` returns the number of bytes that a csvpath has written to `data.cvs`. The `data.csv` file is the stream of matches as the `CsvPath` instance iterates over a delimited file. It includes all matches, or if `match-mode` is set to store unmatched lines, those.

Be aware that `count_bytes()` makes no effort to flush to disk before getting the number of bytes from the OS. It will commonly give numbers that run behind the totally number of bytes that have been directed to be written.


## Examples

```bash
    ~
      name: bytes count
      validation-mode: print, raise, stop
    ~
    $[1*][
        @bytes = count_bytes()
        ~ this mod may be too high for the rate of flush to disk. works
          today for this machine, but not sure it always will ~
        mod(line_number(), 30) == 0 -> print("bytes written so far: $.variables.bytes")
        and.nocontrib(
            lt(@bytes, 1),
            gt(line_number(), 1000))
        -> fail_and_stop()
    ]
```

This csvpath checks the byte count every 30 lines to see if data has gone to disk. If none has by the 1000th line the csvpath fails and stops.

