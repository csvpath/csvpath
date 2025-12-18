
Regex

Matches a regular expression to a string.

The regular expression can be in argument one or two.

Optionally, the third argument returns a group from the match, if any
groups were defined.

| Data signatures                                                             |
|:----------------------------------------------------------------------------|
| regex( all headers: , regex: str )                                          |
| regex( str or regex: strǁ''ǁNone, str or regex: strǁ''ǁNone, [group: int] ) |

| Call signatures                                                                                                                                                         |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| regex( all headers: Headers, regex: TermǁVariableǁHeaderǁFunctionǁReference )                                                                                           |
| regex( str or regex: TermǁVariableǁHeaderǁFunctionǁReference, str or regex: TermǁVariableǁHeaderǁFunctionǁReference, [group: TermǁVariableǁHeaderǁFunctionǁReference] ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | regex() determines if lines match |

| Context          | Qualifier       |
|:-----------------|:----------------|
| Match qualifiers | onmatch, asbool |
| Value qualifiers | onmatch         |


