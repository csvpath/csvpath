
Datetime

datetime() has two purposes.

First, it may indicate that a value must be a {self.name} to be valid. To do this, it must be an argument to a line() and have a header argument.

Alternatively, it may generate a date from a string. Generally, {self.name}() recognizes {self.name}s without needing a format string.

| Data signatures                                  |
|:-------------------------------------------------|
| datetime( date: None|datetime|date )             |
| datetime( date string: None|str, [format: str] ) |

| Call signatures                                                                                                     |
|:--------------------------------------------------------------------------------------------------------------------|
| datetime( date: Header|Variable|Function|Reference )                                                                |
| datetime( date string: Term|Header|Variable|Function|Reference, [format: Term|Header|Function|Variable|Reference] ) |

| Purpose    | Value                                                      |
|:-----------|:-----------------------------------------------------------|
| Main focus | datetime() produces a calculated value and decides matches |
| Type       | Datetime is a line() schema type                           |

| Context          | Qualifier                          |
|:-----------------|:-----------------------------------|
| Match qualifiers | onmatch, notnone, strict, distinct |
| Value qualifiers | onmatch, notnone                   |


