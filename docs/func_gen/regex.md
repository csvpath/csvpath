
## regex()

Regex

Matches a regular expression to a string.

The regular expression can be in argument one or two.

Optionally, the third argument returns a group from the match, if any
groups were defined.

| Data signatures                                                                     |
|:------------------------------------------------------------------------------------|
| regex( all headers: , regex: str )                                                  |
| regex( str or regex: str ǁ '' ǁ None, str or regex: str ǁ '' ǁ None, [group: int] ) |

| Call signatures                                                                                                                                                                                 |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| regex( all headers: Headers, regex: Term ǁ Variable ǁ Header ǁ Function ǁ Reference )                                                                                                           |
| regex( str or regex: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, str or regex: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, [group: Term ǁ Variable ǁ Header ǁ Function ǁ Reference] ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | regex() determines if lines match |

| Context          | Qualifier       |
|:-----------------|:----------------|
| Match qualifiers | onmatch, asbool |
| Value qualifiers | onmatch         |


