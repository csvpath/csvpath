
Date

date() has two purposes.

First, it may indicate that a value must be a {self.name} to be valid. To do this, it must be an argument to a line() and have a header argument.

Alternatively, it may generate a date from a string. Generally, {self.name}() recognizes {self.name}s without needing a format string.

| Data signatures                                |
|:-----------------------------------------------|
| date( date: None ǁ datetime ǁ date )           |
| date( date string: None ǁ str, [format: str] ) |

| Call signatures                                                                                                                 |
|:--------------------------------------------------------------------------------------------------------------------------------|
| date( date: Header ǁ Variable ǁ Function ǁ Reference )                                                                          |
| date( date string: Term ǁ Header ǁ Variable ǁ Function ǁ Reference, [format: Term ǁ Header ǁ Function ǁ Variable ǁ Reference] ) |

| Purpose    | Value                                                  |
|:-----------|:-------------------------------------------------------|
| Main focus | date() produces a calculated value and decides matches |
| Type       | Date is a line() schema type                           |

| Context          | Qualifier                          |
|:-----------------|:-----------------------------------|
| Match qualifiers | onmatch, notnone, strict, distinct |
| Value qualifiers | onmatch, notnone                   |


