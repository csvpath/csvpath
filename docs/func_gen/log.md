
## log()

Writes a message to the CsvPath Framework log at a certain log level.

| Data signatures                                                                             |
|:--------------------------------------------------------------------------------------------|
| log( log this: $${\color{green}str}$$, [info, debug, warn, error: $${\color{green}str}$$] ) |

| Call signatures                                                                                                                                                                                     |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| log( log this: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), [info, debug, warn, error: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term)] ) |

| Purpose                | Value                  |
|:-----------------------|:-----------------------|
| Main focus             | log() is a side-effect |
| Has internal variables | False                  |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
