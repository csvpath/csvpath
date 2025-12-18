
Empty
empty() checks for empty or blank header values in a given line. It
reports True only if all the places it is directed to look are empty.

If you pass it a headers() function it checks for all headers being
empty.

| Data signatures                            |
|:-------------------------------------------|
| empty( Points to the headers: )            |
| empty( Component to check: [36m[3mNone[0m|[36m[3mAny[0m, ... ) |

| Call signatures                                            |
|:-----------------------------------------------------------|
| empty( Points to the headers: [36m[3mHeaders[0m )                    |
| empty( Component to check: [36m[3mVariable[0m|[36m[3mFunction[0m|[36m[3mHeader[0m, ... ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | empty() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


