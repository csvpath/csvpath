
Caps

Alters a string by changing the casing. If the optional second
argument is True the string's words will all be upper-cased.
Otherwise, only the first letter of the string is upper-cased.

The function of capitalizing each contained word is not guaranteed to
preserve spacing, treat punctuation in an ideal way, or handle all
possible special cases.

| Data signatures                                                    |
|:-------------------------------------------------------------------|
| caps( string to modify: str, [if true, init-cap all words: bool] ) |

| Call signatures                                                                                                          |
|:-------------------------------------------------------------------------------------------------------------------------|
| caps( string to modify: Term|Variable|Header|Function|Reference, [if true, init-cap all words: Term|Function|Variable] ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | caps() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


