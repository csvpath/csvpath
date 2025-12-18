
Replace
Replaces the value of the header with another value on every line.

If a header is passed as the first argument its value is replaced.

If a header name or index is passed as the first argument the
identified header's value is replaced.

For example, $[*][@a = line_number() replace(#order_number, @a)]

| Data signatures                                                       |
|:----------------------------------------------------------------------|
| replace( replace value: [36m[3mNone[0m|[36m[3mAny[0m, replacement: [36m[3mAny[0m )                  |
| replace( replace by header identity: [36m[3mint[0m|[36m[3mstr[0m, replacement: [36m[3mNone[0m|[36m[3mAny[0m ) |

| Call signatures                                                                                   |
|:--------------------------------------------------------------------------------------------------|
| replace( replace value: [36m[3mHeader[0m, replacement: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m )            |
| replace( replace by header identity: [36m[3mTerm[0m, replacement: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m ) |

| Purpose    | Value                      |
|:-----------|:---------------------------|
| Main focus | replace() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


