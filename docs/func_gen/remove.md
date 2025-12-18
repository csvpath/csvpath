
## remove()

Remove

This function results in the output of collected lines not including
the header(s) indicated in the argument to remove().

| Data signatures                                                                   |
|:----------------------------------------------------------------------------------|
| remove( header identifier: $${\color{green}int}$$ ǁ $${\color{green}str}$$, ... ) |
| remove( header: $${\color{green}Any}$$, ... )                                     |

| Call signatures                                                                                              |
|:-------------------------------------------------------------------------------------------------------------|
| remove( header identifier: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), ... ) |
| remove( header: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header), ... )        |

| Purpose    | Value                     |
|:-----------|:--------------------------|
| Main focus | remove() is a side-effect |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | onmatch                                                                            |


