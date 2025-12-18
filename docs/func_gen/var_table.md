
## var_table()

Prints a table with all the variable names and values at each line. If
no variable name is passed, table includes all vars. Otherwise, the
vars identified by name are printed.

The table is text formatted.

| Data signatures                   |
|:----------------------------------|
| var_table( [var name: str], ... ) |

| Call signatures                                                                                                                                                                                                                                                                           |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| var_table( [var name: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ Function], ... ) |

| Purpose    | Value                        |
|:-----------|:-----------------------------|
| Main focus | var_table() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


