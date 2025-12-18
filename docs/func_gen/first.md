
## first()

Captures the first line a value or set of values is seen on.

first() stores the first line in a variable using the concatenation of
the values seen as the tracking value.

first() can use a name qualifier as its variable name; otherwise, the
variable name is "first".

| Data signatures                    |
|:-----------------------------------|
| first( header to track: Any, ... ) |

| Call signatures                                                                                               |
|:--------------------------------------------------------------------------------------------------------------|
| first( header to track: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header), ... ) |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | first() produces a calculated value |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |


