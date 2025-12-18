
Decimal

decimal() is a type function often used as an argument to line().

It indicates that the value it receives must be a decimal.

| Data signatures                                                               |
|:------------------------------------------------------------------------------|
| decimal( header: None|str|int, [max: None|float|int], [min: None|float|int] ) |

| Call signatures                                                                                                     |
|:--------------------------------------------------------------------------------------------------------------------|
| decimal( header: Header|Variable|Function|Reference, [max: Term|Function|Variable], [min: Term|Function|Variable] ) |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | decimal() determines if lines match |
| Type       | Decimal is a line() schema type     |

| Context          | Qualifier                          |
|:-----------------|:-----------------------------------|
| Match qualifiers | onmatch, notnone, strict, distinct |
| Value qualifiers | onmatch, notnone, strict           |


