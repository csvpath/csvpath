
## choice()

choice() runs a Jev choice query.

A choice request indicates the strongest selection from a list with a
confidence score. The answer to a choice() is a dict:

{"type": "choice", "choice": chosen-key, "confidence": 0..1,
"probabilities": { key1: 0..1, key2...  } }

The probability key values sum to exactly 1.

Your criteria are in pairs, each a key and a description.
Alternatively, you may use key, none() pairs.

choice() runs within a jev(). It cannot be run standalone. Putting a
choice() outside a jev() results in a built-in CVL error.

Note that using the jev() function requires adding your Jev account
information to config.ini under the [jev] section. As always, we
strongly recommend keeping your credentials in OS environment
variables and using ALL_CAPS form variable names in config.ini to
reference them.

| Data signatures                                                |
|:---------------------------------------------------------------|
| choice( instructions: $${\color{green}str}$$, criteria: dict ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| choice( instructions: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), criteria: JevCriteria ) |

| Purpose                | Value                     |
|:-----------------------|:--------------------------|
| Main focus             | choice() is a side-effect |
| Has internal variables | True                      |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Name qualifier   | optionally expected                                                                                                                                                                                                                            |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
