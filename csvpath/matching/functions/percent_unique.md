
# Percent Unique

Provides a running percentage of the number of unique values in a header.

```bash
    percent_unique(#firstname)
```

This usage returns the percent of unique firstnames that have been found up to the current row. The function tracks values in a variable, by default called `percent_unique`. You can use a qualifier to set another name for the tracking variable.

Percent unique can take an `onmatch` qualifier so that it only tracks uniqueness within the rows matched. If onmatch is not set the percent returned can go above 100%.


## Example

```bash
    [ not(#2 == "Fred")
    @p = percent_unique.last.onmatch(#lastname) ]
```
