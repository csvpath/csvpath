
## boolean()

boolean() is a line() schema type representing a bool value.

To generate a particular bool value use yes() or no().

As you would think, setting distinct limits the number of lines to
four, for practical purposes. Namely: yes(), no(), none(), and a
header name.

| Data signatures                     |
|:------------------------------------|
| boolean( value: None ǁ bool ǁ str ) |

| Call signatures                                                                                                                                                                                                                                                               |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| boolean( value: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ) |

| Purpose    | Value                                                     |
|:-----------|:----------------------------------------------------------|
| Main focus | boolean() produces a calculated value and decides matches |
| Type       | Boolean is a line() schema type                           |

| Context          | Qualifier         |
|:-----------------|:------------------|
| Match qualifiers | onmatch, distinct |
| Value qualifiers | onmatch, notnone  |


