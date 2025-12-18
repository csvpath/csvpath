
## rename()

Rename

Renames one or more headers for the duration of the run.

E.g. rename(#person, "fred") would make it possible to use #fred as
the header

This is most useful for files that have numeric values in the first
line. Setting header names is only syntactic sugar, but it can be
helpful in adding clarity, given that those files require the use of
header indexes to access values.

Rename() can also be a useful buffer if header order is likely to be
correct but header names may drift.

To reset three or more header names in order from left to right add
more names to the function args. However, if you only want to rename
two headers you must use two rename() calls.

Alternatively, you can use a stack variable. For example you could use
a sequence like this to update headers mid-run:     @headers =
headers_stack()     line_number() == 3 -> reset_headers()
line_number() == 6 -> rename(@headers)

Note that renames do not affect other csvpaths, regardless of if they
are run in serial or breadth-first.

| Data signatures                            |
|:-------------------------------------------|
| rename( header: list ǁ tuple )             |
| rename( header: Any, new name: str )       |
| rename( header name: str, new name: str )  |
| rename( header index: int, new name: str ) |
| rename( new header name: str, ... )        |

| Call signatures                                                                                                                                                                             |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| rename( header: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |
| rename( header: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header), new name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) )      |
| rename( header name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), new name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) )     |
| rename( header index: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), new name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) )    |
| rename( new header name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), ... )                                                                                  |

| Purpose    | Value                     |
|:-----------|:--------------------------|
| Main focus | rename() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


