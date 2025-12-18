
## decimal()

Decimal

decimal() is a type function often used as an argument to line().

It indicates that the value it receives must be a decimal.

| Data signatures                                                                           |
|:------------------------------------------------------------------------------------------|
| decimal( header: None ǁ str ǁ int, [max: None ǁ float ǁ int], [min: None ǁ float ǁ int] ) |

| Call signatures                                                                                                                   |
|:----------------------------------------------------------------------------------------------------------------------------------|
| decimal( header: Header ǁ Variable ǁ Function ǁ Reference, [max: Term ǁ Function ǁ Variable], [min: Term ǁ Function ǁ Variable] ) |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | decimal() determines if lines match |
| Type       | Decimal is a line() schema type     |

| Context          | Qualifier                          |
|:-----------------|:-----------------------------------|
| Match qualifiers | onmatch, notnone, strict, distinct |
| Value qualifiers | onmatch, notnone, strict           |


