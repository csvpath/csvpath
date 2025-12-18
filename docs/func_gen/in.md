
In
in() checks if the component value is in the values of the other
arguments.

One advanced in() capability is for lookups in the results of other
named-path group runs.

String terms are treated as possibly | delimited strings of values

| Data signatures                                             |
|:------------------------------------------------------------|
| in( Value to find: [36m[3mNone[0m|[36m[3mAny[0m, Place to look: [36m[3mNone[0m|[36m[3mAny[0m, ... ) |

| Call signatures                                                                                                           |
|:--------------------------------------------------------------------------------------------------------------------------|
| in( Value to find: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, Place to look: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, ... ) |

| Purpose    | Value                          |
|:-----------|:-------------------------------|
| Main focus | in() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


