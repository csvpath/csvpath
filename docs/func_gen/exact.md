
Exact

Looks for an exact match, with unmatched preceding or trailing
characters, of a regular expression to a string.

The regular expression can be in argument one or two.

| Data signatures                                                             |
|:----------------------------------------------------------------------------|
| exact( all headers: , regex: str )                                          |
| exact( str or regex: strǁ''ǁNone, str or regex: strǁ''ǁNone, [group: int] ) |

| Call signatures                                                                                                                                                         |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| exact( all headers: Headers, regex: TermǁVariableǁHeaderǁFunctionǁReference )                                                                                           |
| exact( str or regex: TermǁVariableǁHeaderǁFunctionǁReference, str or regex: TermǁVariableǁHeaderǁFunctionǁReference, [group: TermǁVariableǁHeaderǁFunctionǁReference] ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | exact() determines if lines match |

| Context          | Qualifier       |
|:-----------------|:----------------|
| Match qualifiers | onmatch, asbool |
| Value qualifiers | onmatch         |


