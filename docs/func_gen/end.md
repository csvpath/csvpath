End
Returns the value of the last header.

If an integer argument N is given, the return is the value of the last
header minus N.

I.e., if the last header is #11, end(3) returns the value of header
#8.
| Data signatures                            |
|:-------------------------------------------|
| end( [positions to the left of end: [36m[3mint[0m] ) |
| Call signatures                                                                         |
|:----------------------------------------------------------------------------------------|
| end( [positions to the left of end: [36m[3mTerm[0m|[36m[3mFunction[0m|[36m[3mHeader[0m|[36m[3mVariable[0m|[36m[3mReference[0m|[36m[3mEquality[0m] ) |
| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | end() produces a calculated value |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
