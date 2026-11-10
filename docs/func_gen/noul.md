
## noul()

noul() runs a Jev noul query.

A noul request returns a probability that the answer to the question
provided is "yes".

noul() runs within a jev(). It cannot be run standalone. Putting a
noul() outside a jev() results in a built-in CVL error.

Note that using the jev() function requires adding your Jev account
information to config.ini under the [jev] section. As always, we
strongly recommend keeping your credentials in OS environment
variables and using ALL_CAPS form variable names in config.ini to
reference them.

| Data signatures                                                        |
|:-----------------------------------------------------------------------|
| noul( instructions: $${\color{green}str}$$ )                           |
| noul( instructions: $${\color{green}str}$$, [criteria: NoulCriteria] ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| noul( instructions: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) )                          |
| noul( instructions: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), [criteria: JevCriteria] ) |

| Purpose                | Value                   |
|:-----------------------|:------------------------|
| Main focus             | noul() is a side-effect |
| Has internal variables | True                    |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Name qualifier   | optionally expected                                                                                                                                                                                                                            |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
