
## exact()
Exact

Looks for an exact match, with unmatched preceding or trailing
characters, of a regular expression to a string.

The regular expression can be in argument one or two.

| Data signatures                                                                     |
|:------------------------------------------------------------------------------------|
| exact( all headers: , regex: str )                                                  |
| exact( str or regex: str ǁ '' ǁ None, str or regex: str ǁ '' ǁ None, [group: int] ) |

| Call signatures                                                                                                                                                                                 |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| exact( all headers: Headers, regex: Term ǁ Variable ǁ Header ǁ Function ǁ Reference )                                                                                                           |
| exact( str or regex: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, str or regex: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, [group: Term ǁ Variable ǁ Header ǁ Function ǁ Reference] ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | exact() determines if lines match |

| Context          | Qualifier       |
|:-----------------|:----------------|
| Match qualifiers | onmatch, asbool |
| Value qualifiers | onmatch         |


