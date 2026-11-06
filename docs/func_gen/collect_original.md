
## collect_original()

Copies the registered data file the run started from into the run's
results as the well-known file original.<ext>, byte for byte, e.g.
original.csv, original.xml, original.json, or original.xlsx. It is the
registered file in every source mode: with source-mode: preceding it
is still the registered file, not the preceding csvpath's data.csv.

data.csv is unchanged: it still holds the matched lines.
original.<ext> is fingerprinted in the run's manifest.

The copy is made once, the first time collect_original() is evaluated,
so it can be conditional, e.g. last() -> collect_original(). It always
matches, so rules over a whole XML or JSON document do not need
.nocontrib to keep the original with the results.

collect_original() needs a CsvPaths run. With a CsvPath alone there is
no results directory and it does nothing. Each csvpath in a named-
paths group that calls it gets its own copy. The copy's fingerprint is
checked against the registered file's; a mismatch is reported as an
error and the copy is kept as evidence.

| Data signatures    |
|:-------------------|
| collect_original() |

| Call signatures    |
|:-------------------|
| collect_original() |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | collect_original() is a side-effect |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
