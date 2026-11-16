
## datatype()

datatype() returns the best fitting type for a header value on a given line.
              String is considered the least specific type, meaning that a type is only
              considered a string if all other types do not match. For example, "" is
              considered a none() match and "false" is considered a boolean() match.
            

With the strict qualifier, a value is only a decimal or an integer if
              decimal.strict() or integer.strict() would accept it: "$10.50" and "1,000"
              are strings, not numbers.
            

| Data signatures                                                                                        |
|:-------------------------------------------------------------------------------------------------------|
| datatype( header of value: $${\color{green}str}$$ ǁ $${\color{green}Any}$$ ǁ $${\color{green}None}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                       |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| datatype( header of value: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ) |

| Purpose                | Value                                  |
|:-----------------------|:---------------------------------------|
| Main focus             | datatype() produces a calculated value |
| Has internal variables | False                                  |

| Context          | Qualifier                                                                                                                                                                                                                                                                                                                        |
|:-----------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                                                                                                               |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch), [strict](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#strict) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
