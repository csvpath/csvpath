
## criteria()

criteria() provides further instructions to a Jev noul.

A noul request returns a probability that the answer to the question
provided is "yes".

criteria() is an optional pair of statements, one describing yes, the
other no.

You cannot use a criteria() outside a noul(). For this reason the
criteria() is considered a side effect.

| Data signatures                                                                                                         |
|:------------------------------------------------------------------------------------------------------------------------|
| criteria( Yes means: $${\color{green}str}$$, No means: $${\color{green}str}$$ )                                         |
| criteria( Option: $${\color{green}str}$$, [Choice description: $${\color{green}None}$$ ǁ $${\color{green}str}$$], ... ) |

| Call signatures                                                                                                                                                                                                                                                                            |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| criteria( Yes means: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), No means: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) )                                                                                                    |
| criteria( Option: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), [Choice description: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function)], ... ) |

| Purpose                | Value                       |
|:-----------------------|:----------------------------|
| Main focus             | criteria() is a side-effect |
| Has internal variables | True                        |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Name qualifier   | optionally expected                                                                                                                                                                                                                            |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
