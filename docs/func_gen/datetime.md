Datetime
datetime() has two purposes.
First, it may indicate that a value must be a {self.name} to be valid. To do this, it must be an argument to a line() and have a header argument.
Alternatively, it may generate a date from a string. Generally, {self.name}() recognizes {self.name}s without needing a format string.
| Data signatures                                  |
|:-------------------------------------------------|
| datetime( date: [36m[3mNone[0m|[36m[3mdatetime[0m|[36m[3mdate[0m )             |
| datetime( date string: [36m[3mNone[0m|[36m[3mstr[0m, [format: [36m[3mstr[0m] ) |
| Call signatures                                                                                                     |
|:--------------------------------------------------------------------------------------------------------------------|
| datetime( date: [36m[3mHeader[0m|[36m[3mVariable[0m|[36m[3mFunction[0m|[36m[3mReference[0m )                                                                |
| datetime( date string: [36m[3mTerm[0m|[36m[3mHeader[0m|[36m[3mVariable[0m|[36m[3mFunction[0m|[36m[3mReference[0m, [format: [36m[3mTerm[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mVariable[0m|[36m[3mReference[0m] ) |
| Purpose    | Value                                                      |
|:-----------|:-----------------------------------------------------------|
| Main focus | datetime() produces a calculated value and decides matches |
| Type       | Datetime is a line() schema type                           |
| Context          | Qualifier                          |
|:-----------------|:-----------------------------------|
| Match qualifiers | [36m[3monmatch[0m, [36m[3mnotnone[0m, [36m[3mstrict[0m, [36m[3mdistinct[0m |
| Value qualifiers | [36m[3monmatch[0m, [36m[3mnotnone[0m                   |
