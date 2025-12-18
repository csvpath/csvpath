
## empty()

Empty

empty() checks for empty or blank header values in a given line. It
reports True only if all the places it is directed to look are empty.

If you pass it a headers() function it checks for all headers being
empty.

| Data signatures                              |
|:---------------------------------------------|
| empty( Points to the headers: )              |
| empty( Component to check: None ǁ Any, ... ) |

| Call signatures                                                |
|:---------------------------------------------------------------|
| empty( Points to the headers: Headers )                        |
| empty( Component to check: Variable ǁ Function ǁ Header, ... ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | empty() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


