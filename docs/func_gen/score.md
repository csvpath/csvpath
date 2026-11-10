
## score()

score() runs a Jev score query.

A score request gives the probabilities of items in a list being the
best match. The answer to a score() is a dict:

{'type': 'score', 'score': float, 'confidence': float, 'legend': {0:
str, 1: str, ...}, 'probabilities': {0: 0..1, 1: 0..1, ...}}

 score() runs within a jev(). It cannot be run standalone. Putting a
score() outside a jev() results in a built-in CVL error.

Note that using the jev() function requires adding your Jev account
information to config.ini under the [jev] section. As always, we
strongly recommend keeping your credentials in OS environment
variables and using ALL_CAPS form variable names in config.ini to
reference them.

| Data signatures                                                                                                |
|:---------------------------------------------------------------------------------------------------------------|
| score( instructions: $${\color{green}str}$$, criteria: $${\color{green}None}$$ ǁ $${\color{green}str}$$, ... ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| score( instructions: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), criteria: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), ... ) |

| Purpose                | Value                    |
|:-----------------------|:-------------------------|
| Main focus             | score() is a side-effect |
| Has internal variables | True                     |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Name qualifier   | optionally expected                                                                                                                                                                                                                            |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
