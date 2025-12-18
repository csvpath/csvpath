
## collect()

When collect() is used only values for the indicated headers are
returned during the run. If there are four columns in a data file and
two are collected each line returned by CsvPath.next() will contain
two values.

| Data signatures                                                                    |
|:-----------------------------------------------------------------------------------|
| collect( header identifier: $${\color{green}int}$$ ǁ $${\color{green}str}$$, ... ) |
| collect( header: $${\color{green}Any}$$, ... )                                     |

| Call signatures                                                                                               |
|:--------------------------------------------------------------------------------------------------------------|
| collect( header identifier: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), ... ) |
| collect( header: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header), ... )        |

| Purpose    | Value                      |
|:-----------|:---------------------------|
| Main focus | collect() is a side-effect |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
