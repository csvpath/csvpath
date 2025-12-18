
Integer

integer() is a type function often used as an argument to line().

It indicates that the value it receives must be an integer.

| Data signatures                                                               |
|:------------------------------------------------------------------------------|
| integer( header: None|str|int, [max: None|float|int], [min: None|float|int] ) |

| Call signatures                                                                                                     |
|:--------------------------------------------------------------------------------------------------------------------|
| integer( header: Header|Variable|Function|Reference, [max: Term|Function|Variable], [min: Term|Function|Variable] ) |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | integer() determines if lines match |
| Type       | Integer is a line() schema type     |

| Context          | Qualifier                          |
|:-----------------|:-----------------------------------|
| Match qualifiers | onmatch, notnone, strict, distinct |
| Value qualifiers | onmatch, notnone, strict           |


