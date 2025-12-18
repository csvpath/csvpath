
Size
Returns number of values in a stack variable.

Unless the notnone qualifier is present, the stack is created if not
found.

| Data signatures                |
|:-------------------------------|
| size( stack name: [36m[3mstr[0m )        |
| size( stack: [36m[3mlist[0m|[36m[3mtuple[0m|[36m[3mNone[0m ) |

| Call signatures                                             |
|:------------------------------------------------------------|
| size( stack name: [36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m|[36m[3mTerm[0m ) |
| size( stack: [36m[3mVariable[0m|[36m[3mFunction[0m|[36m[3mReference[0m )                  |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | size() produces a calculated value |
| Aliases    | peek_size, size                    |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | [36m[3monmatch[0m          |
| Value qualifiers | [36m[3monmatch[0m, [36m[3mnotnone[0m |


