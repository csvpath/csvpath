
Exists

exist() does an existance test on match components.

Unlike a simple reference to a match component, also essentially an
existance test, exists() will return True even if there is a value
that evaluates to False. I.e. the False is considered to exist for the
purposes of matching.

| Data signatures                        |
|:---------------------------------------|
| exists( Component to check: None|Any ) |

| Call signatures                                                  |
|:-----------------------------------------------------------------|
| exists( Component to check: Variable|Header|Function|Reference ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | exists() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


