
End

Returns the value of the last header.

If an integer argument N is given, the return is the value of the last
header minus N.

I.e., if the last header is #11, end(3) returns the value of header
#8.

| Data signatures                            |
|:-------------------------------------------|
| end( [positions to the left of end: int] ) |

| Call signatures                                                                                   |
|:--------------------------------------------------------------------------------------------------|
| end( [positions to the left of end: Term ǁ Function ǁ Header ǁ Variable ǁ Reference ǁ Equality] ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | end() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


