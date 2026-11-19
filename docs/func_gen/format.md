
## format()

Uses the Python string formatting mini language.

The format argument is a format spec alone, with no braces and no
leading colon. For example, to format a float to two decimal places:
format(3.14159, ".2f") gives "3.14".

A header value is a string. To format it as a number, convert it
first: format(float(#price), ".2f").

| Data signatures                                                                                   |
|:--------------------------------------------------------------------------------------------------|
| format( value: $${\color{green}None}$$ ǁ $${\color{green}Any}$$, format: $${\color{green}str}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| format( value: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), format: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |

| Purpose                | Value                                |
|:-----------------------|:-------------------------------------|
| Main focus             | format() produces a calculated value |
| Has internal variables | False                                |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
