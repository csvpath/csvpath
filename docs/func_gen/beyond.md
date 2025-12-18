
Beyond

Returns true if the values provided have a between relationship.

The values can be dates, numbers, or strings. They must all be of the
same type.

between() has a number of aliases. One of them may work better
syntactically in your use case, but they are all the same logic.

| Data signatures                                                                                   |
|:--------------------------------------------------------------------------------------------------|
| beyond( The value to test: Noneǁdatetimeǁdate, From: Noneǁdatetimeǁdate, To: Noneǁdatetimeǁdate ) |
| beyond( The value to test: Noneǁfloatǁint, From: Noneǁfloatǁint, To: Noneǁfloatǁint )             |
| beyond( The value to test: Noneǁstr, From: Noneǁstr, To: Noneǁstr )                               |

| Call signatures                                                                                                                                                  |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| beyond( The value to test: TermǁVariableǁHeaderǁFunctionǁReference, From: TermǁVariableǁHeaderǁFunctionǁReference, To: TermǁVariableǁHeaderǁFunctionǁReference ) |
| beyond( The value to test: TermǁVariableǁHeaderǁFunctionǁReference, From: TermǁVariableǁHeaderǁFunctionǁReference, To: TermǁVariableǁHeaderǁFunctionǁReference ) |
| beyond( The value to test: TermǁVariableǁHeaderǁFunctionǁReference, From: TermǁVariableǁHeaderǁFunctionǁReference, To: TermǁVariableǁHeaderǁFunctionǁReference ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | beyond() determines if lines match |
| Aliases    | beyond, outside, before_after      |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


