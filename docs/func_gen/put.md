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
| put( new var name: [36m[3mstr[0m )                                     |
| put( var name: [36m[3mstr[0m, var value: [36m[3mAny[0m )                         |
| put( var name: [36m[3mstr[0m, tracking key: [36m[3mstr[0m, tracking value: [36m[3mAny[0m ) |
| Call signatures                                                                                                                                                          |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| put( new var name: [36m[3mTerm[0m )                                                                                                                                                |
| put( var name: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, var value: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m )                                                             |
| put( var name: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, tracking key: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, tracking value: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m ) |
| Purpose    | Value                  |
|:-----------|:-----------------------|
| Main focus | put() is a side-effect |
| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |
