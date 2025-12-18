
Empty stack

If no arguments are provided, adds the names of any headers without
values to a stack. If one or more arguments are provided and an
argument is a variable that variable is checked for emptyness.

Header and variable arguments can be mixed.

The resulting stack does not persist from line to line.

| Data signatures                               |
|:----------------------------------------------|
| empty_stack()                                 |
| empty_stack( [header or var: None|Any], ... ) |

| Call signatures                                      |
|:-----------------------------------------------------|
| empty_stack()                                        |
| empty_stack( [header or var: Variable|Header], ... ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | empty_stack() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


