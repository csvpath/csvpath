
Put

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

| Call signatures                                                                                                                                                          |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| put( new var name: Term )                                                                                                                                                |
| put( var name: TermǁVariableǁHeaderǁFunctionǁReference, var value: TermǁVariableǁHeaderǁFunctionǁReference )                                                             |
| put( var name: TermǁVariableǁHeaderǁFunctionǁReference, tracking key: TermǁVariableǁHeaderǁFunctionǁReference, tracking value: TermǁVariableǁHeaderǁFunctionǁReference ) |

| Purpose    | Value                  |
|:-----------|:-----------------------|
| Main focus | put() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


