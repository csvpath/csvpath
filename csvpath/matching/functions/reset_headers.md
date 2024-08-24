
# Reset Headers

`reset_headers()` swaps the current row values in for the headers. The original headers are just the 0th line values. In many CSVs there is other data at the top or multiple sets of headers at different points in the file. Calling `reset_headers()` when you recognize a change in the data gives you a way to adjust for those breaks.

This function is experimental. It seems to work fine and logically it should. But headers are a core part of CsvPath and it is possible a corner case might be affected by a header reset. Use caution and test your csvpaths well!


## Example

```bash
    ${PATH}[*][
        gt(count_headers_in_line(),  count_headers()) -> reset_headers()
        push("last_header", end())
    ]
```

This csvpath resets the headers when there are more headers in a given line then there were in the header row (0th line). It pushes the value of the last header onto a stack for inspection.


