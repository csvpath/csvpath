
## headers()

Directs certain functions, such as any(), to search in the headers.
variables() has the same function, but directing the search to the
variables.

This function can also do an existance test, but that capability has
been replaced by header_name() and header_index().

| Data signatures                                                               |
|:------------------------------------------------------------------------------|
| headers( [depreciated arg: $${\color{green}str}$$ ǁ $${\color{green}int}$$] ) |

| Call signatures                                                                                                                                                                                                                                                                    |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| headers( [depreciated arg: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function)] ) |

| Purpose    | Value                      |
|:-----------|:---------------------------|
| Main focus | headers() is a side-effect |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
