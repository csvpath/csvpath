
## peek_size()

Returns number of values in a stack variable.

Unless the notnone qualifier is present, the stack is created if not
found.

| Data signatures                         |
|:----------------------------------------|
| peek_size( stack name: str )            |
| peek_size( stack: list ǁ tuple ǁ None ) |

| Call signatures                                                          |
|:-------------------------------------------------------------------------|
| peek_size( stack name: Variable ǁ Header ǁ Function ǁ Reference ǁ Term ) |
| peek_size( stack: Variable ǁ Function ǁ Reference )                      |

| Purpose    | Value                                   |
|:-----------|:----------------------------------------|
| Main focus | peek_size() produces a calculated value |
| Aliases    | peek_size, size                         |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


