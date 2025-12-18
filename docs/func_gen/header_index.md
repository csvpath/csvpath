
## header_index()
Header index

Looks up a header index by header name. e.g. header_index("firstname")
returns 0 when the "firstname" header is first.
header_index("lastname", 1) returns True if the "lastname" header is
second.

If given an expected result as a 2nd argument the return is True/False
on the match of expected to actual

If no value is provided, header_index() is an existance test for the
header, not a check for the line having a value for the header.

| Data signatures                                                            |
|:---------------------------------------------------------------------------|
| header_index( header identity: str ǁ int, [value check: None ǁ Any ǁ ''] ) |

| Call signatures                                                                  |
|:---------------------------------------------------------------------------------|
| header_index( header identity: Term ǁ Function ǁ Variable, [value check: Term] ) |

| Purpose    | Value                                      |
|:-----------|:-------------------------------------------|
| Main focus | header_index() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


