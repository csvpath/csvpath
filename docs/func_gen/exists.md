
Exists
exist() does an existance test on match components.

Unlike a simple reference to a match component, also essentially an
existance test, exists() will return True even if there is a value
that evaluates to False. I.e. the False is considered to exist for the
purposes of matching.

| Data signatures                        |
|:---------------------------------------|
| exists( Component to check: [36m[3mNone[0m|[36m[3mAny[0m ) |

| Call signatures                                                  |
|:-----------------------------------------------------------------|
| exists( Component to check: [36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | exists() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


