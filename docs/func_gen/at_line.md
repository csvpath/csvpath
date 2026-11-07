
## at_line()

True if the current line is the argument or among the arguments of
this function.

| Data signatures                                |
|:-----------------------------------------------|
| at_line( this line: $${\color{green}int}$$ )   |
| at_line( a line: $${\color{green}int}$$, ... ) |

| Call signatures                                                                                                                                                                         |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| at_line( this line: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) )   |
| at_line( a line: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), ... ) |

| Purpose                | Value                               |
|:-----------------------|:------------------------------------|
| Main focus             | at_line() determines if lines match |
| Has internal variables | False                               |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
