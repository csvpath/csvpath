
## too_long()

too_long() and min_length() are True when the value has at least the
given number of characters. too_short() and max_length() are True when
it has at most that number.

Read too_long(#name, 5) as "a value that is 5 characters is too long
for this field": the value must be 4 or fewer characters to pass.
too_short(#name, 5) is True for a value of 5 or fewer characters.

| Data signatures                                                 |
|:----------------------------------------------------------------|
| too_long( $${\color{green}str}$$ ǁ '', $${\color{green}int}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| too_long( [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |

| Purpose                | Value                                  |
|:-----------------------|:---------------------------------------|
| Main focus             | too_long() produces a calculated value |
| Has internal variables | False                                  |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
