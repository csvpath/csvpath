
# Replace

Replaces a header value with another value.

`replace()` takes two arguments. The first argument is the name or index of the header value to be replaced. The second argument generates the replacement value.

The replaced values will be seen in the lines iteration from either CsvPaths or CsvPath. It will also be seen in the named-results collected by the results manager, if you are running CsvPaths and are collecting lines. That means your transformed results would then be accessible by reference from other csvpaths.

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

