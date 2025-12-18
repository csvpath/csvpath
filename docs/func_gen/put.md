
## put()

Sets a variable that tracks keyed-values.

A tracking value is similar to a dictionary key. It usually keys a
count, calculation, or transformation.

Calling put() with one argument, a var name, creates an empty
dictionary.

Calling put() with two arguments creates a regular named-value
variable.

Calling put() with three arguments creates a dictionary, if needed,
and uses the second variable as the key to store and access the third.

While get() and put() make it possible to create and use tracking-
value variables in an ad hoc dict-like way, using a more specific
function is often simpler.

| Data signatures                                              |
|:-------------------------------------------------------------|
| put( new var name: str )                                     |
| put( var name: str, var value: Any )                         |
| put( var name: str, tracking key: str, tracking value: Any ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| put( new var name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) )                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| put( var name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), var value: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) )                                                                                                                                                                                                                                                                                                                                                                        |
| put( var name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), tracking key: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), tracking value: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |

| Purpose    | Value                  |
|:-----------|:-----------------------|
| Main focus | put() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


