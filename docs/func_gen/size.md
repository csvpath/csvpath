
Size

Returns number of values in a stack variable.

Unless the notnone qualifier is present, the stack is created if not
found.

| Data signatures                |
|:-------------------------------|
| size( stack name: str )        |
| size( stack: listǁtupleǁNone ) |

| Call signatures                                             |
|:------------------------------------------------------------|
| size( stack name: VariableǁHeaderǁFunctionǁReferenceǁTerm ) |
| size( stack: VariableǁFunctionǁReference )                  |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | size() produces a calculated value |
| Aliases    | peek_size, size                    |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


