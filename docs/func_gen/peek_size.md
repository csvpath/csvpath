
Peek size

Returns number of values in a stack variable.

Unless the notnone qualifier is present, the stack is created if not
found.

| Data signatures                     |
|:------------------------------------|
| peek_size( stack name: str )        |
| peek_size( stack: listǁtupleǁNone ) |

| Call signatures                                                  |
|:-----------------------------------------------------------------|
| peek_size( stack name: VariableǁHeaderǁFunctionǁReferenceǁTerm ) |
| peek_size( stack: VariableǁFunctionǁReference )                  |

| Purpose    | Value                                   |
|:-----------|:----------------------------------------|
| Main focus | peek_size() produces a calculated value |
| Aliases    | peek_size, size                         |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


