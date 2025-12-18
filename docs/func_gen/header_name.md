
Header name
Looks up a header name by index. e.g. header_name(0, "firstname")
returns True if the first header is "firstname".

If given an expected result as a 2nd argument the return is True/False
on the match of expected to actual

If no value is provided, header_name() is an existance test for the
header, not a check for the line having a value for the header.

| Data signatures                                                     |
|:--------------------------------------------------------------------|
| header_name( header identity: [36m[3mstr[0m|[36m[3mint[0m, [value check: [36m[3mNone[0m|[36m[3mAny[0m|[36m[3m''[0m] ) |

| Call signatures                                                             |
|:----------------------------------------------------------------------------|
| header_name( header identity: [36m[3mTerm[0m|[36m[3mFunction[0m|[36m[3mVariable[0m, [value check: [36m[3mTerm[0m] ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | header_name() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


