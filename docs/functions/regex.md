
# Regular Expressions

Regular expressions allow you to match against values found in headers, variables, and functions. CsvPath uses <a href='https://docs.python.org/3/library/re.html'>Python's built-in regex capabilities</a>.

Within the CsvPaths grammar, regexes are plain text wrapped in forward slashes. E.g. `/^my( )regex/`. The syntax is enforced by Python's regex parser. CsvPaths checks its capacity to host regexes against the Python regex unit tests. While there are a small number of corner cases, you should be able use your regular expressions unchanged.

At the moment, regular expressions are only acted on in the `regex()` and `exact()` functions. The functions find matches and return the first matched text. You can optionally add an int, as a third argument, to return the capture group at that index. Capture groups are 1-based; 0 means the whole matched string, which is the default returned without an index.

The syntax of `regex()` is:
```regex
regex( /[A-Z][a-z]*( jr\.?)?/, #firstname, 1 )`
```

## regex()

`regex()` matches within the value it is run against. If there is any match it is returned. If you add an int arg indicating a capture group, only that group's value will be returned.

## exact()

`exact()` uses the same regular expression capability but returns a `bool`. `True` if the regex string is an exact match for the whole of the value; otherwise, `False`.

## Examples

```bash
    $[*][
        regex(/s(niff)le/, #say)
        @group1.onmatch = regex(/s(niff)le/, #say, 1)
    ]
```

This regex sets the `group1` variable to `niff` when the regex `/s(niff)le/` matches. This is an example of a match component having distinct matching and value-producing roles. The first use of `regex()` limits the match to a single row of the test CSV file. The second use of `regex()` produces a value for assignment to `@group1`. The variable is only set on matched rows because it has the `onmatch` qualifier.

The result is that `@group1` is set to `niff`.



