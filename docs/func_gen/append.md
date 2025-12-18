
## append()

Append

Adds the header name and a value to the end of every line. The name is
added to the headers and available for use in the csvpath. An appended
header becomes part of the headers when it is first set. If The
append() is conditional to a when/do operator there could be lines
that do not have the appended header; however, after the first
appended line all lines have the appended header.

| Data signatures                                                                                          |
|:---------------------------------------------------------------------------------------------------------|
| append( name of appended header: str, value: None ǁ Any, [append header name to header row data: bool] ) |

| Call signatures                                                                                                                                           |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------|
| append( name of appended header: Term, value: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, [append header name to header row data: Term ǁ Function] ) |

| Purpose    | Value                     |
|:-----------|:--------------------------|
| Main focus | append() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


