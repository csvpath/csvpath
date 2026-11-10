
## jev()

jev() creates runs Jev queries to get probability determinations from
the Jev System One model.

A jev() function has a context, referred to as "state", and contains
one or more functions that implement Jev API calls.

- noul() answers a yes/no question formulated as a yes confirmation.
noul() results in a float confidence score.

- choice() classifies an input according to classes provided by the
function. choice()'s output is a dict.

- score() returns a score, probability, and confidence against leveled
options. score()'s output is a dict.

The jev() operation results in a stack variable containing one item
for each query, collectively telling you about the state. The
individual answers can be accessed using the stack variable functions,
get() and put(), and jsonpath()

If you provide a name qualifier the results variable will take that
name. For example, if your function is jev.myqueries(), the results
variable will be named myqueries. If you do not provide a name
qualifier the results will be available under a "jev" variable.

Note that results are only saved in a variable when you use jev()
standalone. If you assign jev() to a variable explicitly the function
will not create its own separate variable.

Using the jev() function requires adding your Jev account information
to config.ini in a key named "key" under the [jev] section. As always,
we strongly recommend keeping your credentials in OS environment
variables and using ALL_CAPS form variable names in config.ini to
reference them.

| Data signatures                                                                                    |
|:---------------------------------------------------------------------------------------------------|
| jev( state: $${\color{green}str}$$, query: $${\color{green}None}$$ ǁ $${\color{green}Any}$$, ... ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| jev( state: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), query: JevNoul ǁ JevChoice ǁ JevScore, ... ) |

| Purpose                | Value                  |
|:-----------------------|:-----------------------|
| Main focus             | jev() is a side-effect |
| Has internal variables | True                   |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Name qualifier   | optionally expected                                                                                                                                                                                                                            |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
