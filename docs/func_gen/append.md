Append
Adds the header name and a value to the end of every line. The name is
added to the headers and available for use in the csvpath. An appended
header becomes part of the headers when it is first set. If The
append() is conditional to a when/do operator there could be lines
that do not have the appended header; however, after the first
appended line all lines have the appended header.
| Data signatures                                                                                        |
|:-------------------------------------------------------------------------------------------------------|
| append( name of appended header: [36m[3mstr[0m, value: [36m[3mNone[0m|[36m[3mAny[0m, [append header name to header row data: [36m[3mbool[0m] ) |
| Call signatures                                                                                                                                 |
|:------------------------------------------------------------------------------------------------------------------------------------------------|
| append( name of appended header: [36m[3mTerm[0m, value: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, [append header name to header row data: [36m[3mTerm[0m|[36m[3mFunction[0m] ) |
| Purpose    | Value                     |
|:-----------|:--------------------------|
| Main focus | append() is a side-effect |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
