
Empty stack
If no arguments are provided, adds the names of any headers without
values to a stack. If one or more arguments are provided and an
argument is a variable that variable is checked for emptyness.

Header and variable arguments can be mixed.

The resulting stack does not persist from line to line.

| Data signatures                               |
|:----------------------------------------------|
| empty_stack()                                 |
| empty_stack( [header or var: [36m[3mNone[0m|[36m[3mAny[0m], ... ) |

| Call signatures                                      |
|:-----------------------------------------------------|
| empty_stack()                                        |
| empty_stack( [header or var: [36m[3mVariable[0m|[36m[3mHeader[0m], ... ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | empty_stack() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


