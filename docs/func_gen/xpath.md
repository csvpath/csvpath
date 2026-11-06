
## xpath()

Finds the value of an XPath expression given a match component
containing XML. A path that selects one node gives that node's value,
several nodes give a list of their values, and no nodes give an empty
list, as with jsonpath(). XPath functions like count(), boolean(), and
string() give their result.

With only an XPath, xpath() evaluates the whole data file as one XML
document, for rules-based validation of XML files. Each xpath()
evaluates the document on one line only: scan [*] and make stop() the
last match component, or scan [0] if the file does not start with a
blank line. Use .nocontrib on rules like
xpath.nocontrib("/orders/order[not(sku)]") -> print("...", fail()) so
that a conforming document still matches. The run's data is a copy of
the document.

| Data signatures                                                                                                          |
|:-------------------------------------------------------------------------------------------------------------------------|
| xpath( from this XML: $${\color{green}str}$$ ǁ '' ǁ $${\color{green}None}$$, select this XPath: $${\color{green}str}$$ ) |
| xpath( select this XPath in the whole document: $${\color{green}str}$$ )                                                 |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| xpath( from this XML: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), select this XPath: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |
| xpath( select this XPath in the whole document: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) )                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | xpath() produces a calculated value |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
