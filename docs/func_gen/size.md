
Size

Returns number of values in a stack variable.

Unless the notnone qualifier is present, the stack is created if not
found.

| Data signatures                |
|:-------------------------------|
| size( stack name: str )        |
| size( stack: list|tuple|None ) |

| Call signatures                                             |
|:------------------------------------------------------------|
| size( stack name: Variable|Header|Function|Reference|Term ) |
| size( stack: Variable|Function|Reference )                  |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | size() produces a calculated value |
| Aliases    | peek_size, size                    |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


