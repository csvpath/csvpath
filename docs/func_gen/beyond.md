
Beyond

Returns true if the values provided have a between relationship.

The values can be dates, numbers, or strings. They must all be of the
same type.

between() has a number of aliases. One of them may work better
syntactically in your use case, but they are all the same logic.

| Data signatures                                                                                               |
|:--------------------------------------------------------------------------------------------------------------|
| beyond( The value to test: None ǁ datetime ǁ date, From: None ǁ datetime ǁ date, To: None ǁ datetime ǁ date ) |
| beyond( The value to test: None ǁ float ǁ int, From: None ǁ float ǁ int, To: None ǁ float ǁ int )             |
| beyond( The value to test: None ǁ str, From: None ǁ str, To: None ǁ str )                                     |

| Call signatures                                                                                                                                                                          |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| beyond( The value to test: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, From: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, To: Term ǁ Variable ǁ Header ǁ Function ǁ Reference ) |
| beyond( The value to test: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, From: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, To: Term ǁ Variable ǁ Header ǁ Function ǁ Reference ) |
| beyond( The value to test: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, From: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, To: Term ǁ Variable ǁ Header ǁ Function ǁ Reference ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | beyond() determines if lines match |
| Aliases    | beyond, outside, before_after      |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


