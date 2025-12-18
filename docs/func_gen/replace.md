
## replace()

Replace

Replaces the value of the header with another value on every line.

If a header is passed as the first argument its value is replaced.

If a header name or index is passed as the first argument the
identified header's value is replaced.

For example, $[*][@a = line_number() replace(#order_number, @a)]

| Data signatures                                                           |
|:--------------------------------------------------------------------------|
| replace( replace value: None ǁ Any, replacement: Any )                    |
| replace( replace by header identity: int ǁ str, replacement: None ǁ Any ) |

| Call signatures                                                                                           |
|:----------------------------------------------------------------------------------------------------------|
| replace( replace value: Header, replacement: Term ǁ Variable ǁ Header ǁ Function ǁ Reference )            |
| replace( replace by header identity: Term, replacement: Term ǁ Variable ǁ Header ǁ Function ǁ Reference ) |

| Purpose    | Value                      |
|:-----------|:---------------------------|
| Main focus | replace() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


