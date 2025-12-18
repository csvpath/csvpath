
## counter()
Increments a variable. The increment is 1 by default.

Counters must be named using a name qualifier. Without that, the ID
generated for your counter will be tough to use.

A name qualifier is an arbitrary name added with a dot after the
function name and before the parentheses. It looks like
counter.my_name()

| Data signatures                          |
|:-----------------------------------------|
| counter( [amount to increment by: int] ) |

| Call signatures                                                                                 |
|:------------------------------------------------------------------------------------------------|
| counter( [amount to increment by: Term ǁ Function ǁ Header ǁ Variable ǁ Reference ǁ Equality] ) |

| Purpose    | Value                                 |
|:-----------|:--------------------------------------|
| Main focus | counter() produces a calculated value |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |


