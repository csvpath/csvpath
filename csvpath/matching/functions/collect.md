
# Collect

`collect()` identifies headers CsvPath should collect when a row matches. The headers can be given as their 0-based index or by name. The name of a header is whatever value is found in that column in line 0. `collect()` only affects the csvpath it is used in.

If you are running multiple csvpaths on a single file using a `CsvPaths` object, each csvpath has its own `CsvPath` object. The set of `CsvPath` objects are collectively managed by the `CsvPaths` object. Each `CsvPath` object will collect the values of either all headers or just the ones identified by a `collect()` in its csvpath. This means that potentially each csvpath returns a different set of headers to the `CsvPaths`.

Keep in mind that `collect()` doesn't have any impact on `print()` and `jinja()`. Those functions still have access to the values of all the headers.

That all sounds complicated! Just remember the core idea: each csvpath returns the values of the headers identified by `collect()`, or if there is no `collect()` all the header values.


## Examples

```bash
    $[1*][
        collect(0, "say")
    ]
```

This csvpath collects the values of the first header and the header named `"say"`. If it is collecting lines from the test file at `tests/test_resources/test.csv` it is taking two out of three columns. The resulting data might look like:

```python
    ['Kermit', 'Ribbit']
    ['Fish', 'Glug glug']
    ['Ant', 'Snicker']
```



