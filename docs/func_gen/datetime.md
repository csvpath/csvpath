
Datetime

datetime() has two purposes.

First, it may indicate that a value must be a {self.name} to be valid. To do this, it must be an argument to a line() and have a header argument.

Alternatively, it may generate a date from a string. Generally, {self.name}() recognizes {self.name}s without needing a format string.

| Data signatures                                  |
|:-------------------------------------------------|
| datetime( date: Noneǁdatetimeǁdate )             |
| datetime( date string: Noneǁstr, [format: str] ) |

| Call signatures                                                                                                     |
|:--------------------------------------------------------------------------------------------------------------------|
| datetime( date: HeaderǁVariableǁFunctionǁReference )                                                                |
| datetime( date string: TermǁHeaderǁVariableǁFunctionǁReference, [format: TermǁHeaderǁFunctionǁVariableǁReference] ) |

| Purpose    | Value                                                      |
|:-----------|:-----------------------------------------------------------|
| Main focus | datetime() produces a calculated value and decides matches |
| Type       | Datetime is a line() schema type                           |

| Context          | Qualifier                          |
|:-----------------|:-----------------------------------|
| Match qualifiers | onmatch, notnone, strict, distinct |
| Value qualifiers | onmatch, notnone                   |


