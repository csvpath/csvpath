
## get()

Get

Returns a variable's tracking or index value. The variable is either:
- found by name using string value of the first argument, or - a
variable or reference that is a dictionary or stack

A tracking value is similar to a dictionary key, usually keying a
count, calculation, or transformation.

An index is the 0-based position number of an item in a stack
variable. Stack variables are like lists or tuples.

While get() and put() make it possible to create and use tracking-
value variables in an ad hoc dict-like way, this is not recommended
unless there is no simplier solution based on more specific functions.

| Data signatures                                                                                                                      |
|:-------------------------------------------------------------------------------------------------------------------------------------|
| get( var name: str ǁ dict, [tracking value: None ǁ str ǁ int ǁ float ǁ bool ǁ ''], [default: None ǁ str ǁ int ǁ float ǁ bool ǁ ''] ) |

| Call signatures                                                                                                                                                         |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| get( var name: Header ǁ Term ǁ Function ǁ Variable ǁ Reference, [tracking value: Header ǁ Term ǁ Function ǁ Variable], [default: Header ǁ Term ǁ Function ǁ Variable] ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | get() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


