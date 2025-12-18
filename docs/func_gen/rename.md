
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
| rename( header: [36m[3mlist[0m|[36m[3mtuple[0m )               |
| rename( header: [36m[3mAny[0m, new name: [36m[3mstr[0m )       |
| rename( header name: [36m[3mstr[0m, new name: [36m[3mstr[0m )  |
| rename( header index: [36m[3mint[0m, new name: [36m[3mstr[0m ) |
| rename( new header name: [36m[3mstr[0m, ... )        |

| Call signatures                              |
|:---------------------------------------------|
| rename( header: [36m[3mVariable[0m|[36m[3mReference[0m )         |
| rename( header: [36m[3mHeader[0m, new name: [36m[3mTerm[0m )     |
| rename( header name: [36m[3mTerm[0m, new name: [36m[3mTerm[0m )  |
| rename( header index: [36m[3mTerm[0m, new name: [36m[3mTerm[0m ) |
| rename( new header name: [36m[3mTerm[0m, ... )         |

| Purpose    | Value                     |
|:-----------|:--------------------------|
| Main focus | rename() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


