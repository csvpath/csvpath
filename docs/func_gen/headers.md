
## headers()

Directs certain functions, such as any(), to search in the headers.
variables() has the same function, but directing the search to the
variables.

This function can also do an existance test, but that capability has
been replaced by header_name() and header_index().

| Data signatures                         |
|:----------------------------------------|
| headers( [depreciated arg: str ǁ int] ) |

| Call signatures                                          |
|:---------------------------------------------------------|
| headers( [depreciated arg: Term ǁ Variable ǁ Function] ) |

| Purpose    | Value                      |
|:-----------|:---------------------------|
| Main focus | headers() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


