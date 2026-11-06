
## jsonpath()

Finds the value of an JSONPath expression given a match component
containing JSON.

With only a JSONPath, jsonpath() evaluates the whole data file as one
JSON document, for rules-based validation of JSON files. Each
jsonpath() evaluates the document on one line only: scan [*] and make
stop() the last match component, or scan [0]. Use .nocontrib on rules
like jsonpath.nocontrib("$.orders[?(@.qty < 1)]") -> print("...",
fail()) so that a conforming document still matches. The run's data is
the JSON document.

| Data signatures                                                                                                                 |
|:--------------------------------------------------------------------------------------------------------------------------------|
| jsonpath( from this JSON: $${\color{green}Any}$$ ǁ '' ǁ $${\color{green}None}$$, select this JSONPath: $${\color{green}str}$$ ) |
| jsonpath( select this JSONPath in the whole document: $${\color{green}str}$$ )                                                  |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| jsonpath( from this JSON: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), select this JSONPath: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |
| jsonpath( select this JSONPath in the whole document: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) )                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

| Purpose    | Value                                  |
|:-----------|:---------------------------------------|
| Main focus | jsonpath() produces a calculated value |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
