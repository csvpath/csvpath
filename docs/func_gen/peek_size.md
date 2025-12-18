
Peek size

Returns number of values in a stack variable.

Unless the notnone qualifier is present, the stack is created if not
found.

| Data signatures                     |
|:------------------------------------|
| peek_size( stack name: str )        |
| peek_size( stack: list|tuple|None ) |

| Call signatures                                                  |
|:-----------------------------------------------------------------|
| peek_size( stack name: Variable|Header|Function|Reference|Term ) |
| peek_size( stack: Variable|Function|Reference )                  |

| Purpose    | Value                                   |
|:-----------|:----------------------------------------|
| Main focus | peek_size() produces a calculated value |
| Aliases    | peek_size, size                         |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


