
Inside

Returns true if the values provided have a between relationship.

The values can be dates, numbers, or strings. They must all be of the
same type.

between() has a number of aliases. One of them may work better
syntactically in your use case, but they are all the same logic.

| Data signatures                                                                                   |
|:--------------------------------------------------------------------------------------------------|
| inside( The value to test: None|datetime|date, From: None|datetime|date, To: None|datetime|date ) |
| inside( The value to test: None|float|int, From: None|float|int, To: None|float|int )             |
| inside( The value to test: None|str, From: None|str, To: None|str )                               |

| Call signatures                                                                                                                                                  |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| inside( The value to test: Term|Variable|Header|Function|Reference, From: Term|Variable|Header|Function|Reference, To: Term|Variable|Header|Function|Reference ) |
| inside( The value to test: Term|Variable|Header|Function|Reference, From: Term|Variable|Header|Function|Reference, To: Term|Variable|Header|Function|Reference ) |
| inside( The value to test: Term|Variable|Header|Function|Reference, From: Term|Variable|Header|Function|Reference, To: Term|Variable|Header|Function|Reference ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | inside() determines if lines match |
| Aliases    | between, inside, from_to, range    |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


