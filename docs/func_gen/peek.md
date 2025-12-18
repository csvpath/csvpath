
Peek

Returns a value at a stack variable index, but does not remove it.

The stack is created if not found.

| Data signatures                     |
|:------------------------------------|
| peek( stack name: str, index: int ) |

| Call signatures                                                          |
|:-------------------------------------------------------------------------|
| peek( stack name: Term|Variable|Header|Function|Reference, index: Term ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | peek() produces a calculated value |

| Context          | Qualifier       |
|:-----------------|:----------------|
| Match qualifiers | onmatch, asbool |
| Value qualifiers | onmatch         |


