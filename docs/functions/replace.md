
# Replace, Insert, and Append

### Replace
`replace()` replaces a header value with another value. It takes two arguments:
- The header or the name or index of the header whose value will be replaced
- The replacement value

The replaced values will be seen in the lines iteration from either CsvPaths or CsvPath. It will also be seen in the named-results collected by the results manager, if you are running CsvPaths and are collecting lines. That means your transformed results would then be accessible by reference from other csvpaths.

### Insert
`insert()` inserts a new header at an index and inserts the values of that header for every line. Arguments are:
- The index the header should be inserted. 2 would mean the new header would be the 3rd header -- remember that header indexes are 0-based.
- The name of the header. The header's name does not have to appear in the results. But it does need to exist to help the function track if it has been inserted or not.
- The value that should be inserted in the header's position on every line. This can be a variable, header, function, or reference.

### Append
`append()` attaches a new value under a new header to the end of the line. Like with `replace()`, the new value will be visible to any siblings below a `CsvPaths` instance if the run is by-line; a.k.a. breadth-first or parallel.


## Examples

```bash
    $[*][ replace(#1, upper(#1)) ]
```
This csvpath transforms the 1-header value (0-based, so 2nd header) to uppercase.

```bash
    $[*][
        gt(length(#3), 12) ->
                replace(#1, concat(substring(#3, 10), "...")) ]
```
Here we truncate any value in the 4th header values and add an ellipse.

```bash

    $test[*]
    [
        firstline.nocontrib() -> append("rnd_id", "rnd_id")
        not.nocontrib( firstline() ) -> append("rnd_id", shuffle())
        print_line()
    ]
```

This csvpath creates a new CSV file on the command line with a new column at the end of every line. The new column contains a random number in the range 0 to the number of data lines in the file being iterated.

To generate a CSV file from this csvpath you would want to do something like:

```bash
    python create_new_file.py > new.csv
```

The Python would be something like:

```python
    from csvpath import CsvPath
    path = CsvPath().parse(cvspathstr)
    path.fast_forward()
```

If you used CsvPaths you would need two more lines of Python, but you could do something more programmatic with the results. You would pull the results from the `ResultsManager` and work with the printout lines or the captured data lines.

