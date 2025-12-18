
Any

any() returns True if at least one contained match component matches a
given value.

With no arguments any() matches if there are values in any variable or
header.

With a single headers() or variables() function any() returns True if
there is a match component of the the type indicated with a value.

With a second argument the test is for the specific value in any match
component of the indicated type.

any() is similar to or() or OR logic. While any() gives you more fine-
grained control, remember that you can also use logic-mode to
configure a csvpath to use OR as the basis for matching.

| Data signatures                                         |
|:--------------------------------------------------------|
| any()                                                   |
| any( where to look: None|Any, value to find: None|Any ) |
| any( where to look: None|Any )                          |

| Call signatures                                                                                          |
|:---------------------------------------------------------------------------------------------------------|
| any()                                                                                                    |
| any( where to look: Variables|Headers, value to find: Term|Function|Header|Variable|Reference|Equality ) |
| any( where to look: Variables|Headers|Term|Function|Header|Variable|Reference|Equality )                 |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | any() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


