
## print_line()

Prints the current line as delimited data.

print_line() only prints collected headers. That is, if you use the
collect() function to limit the headers you are collecting,
print_line() respects that choice.

print_line() will output replaced data if print_line() comes after a
replace().

Use the optional arguments to pass a printouts stream, delimiter
and/or quotechar. If a quote char is provided it will be used with
every header value, regardless of technical need. At this time
print_line() does not attempt to guess delimiters and/or quotechars or
use quotechars in a proactive way.

Printing to a dedicated printer can help create stand-alone data-ready
output. That option is mainly valuable in named-paths group runs where
printers' printouts are more clearly separated.

| Data signatures                                                                                                         |
|:------------------------------------------------------------------------------------------------------------------------|
| print_line()                                                                                                            |
| print_line( printer: $${\color{green}str}$$, [delimiter: $${\color{green}str}$$], [quotechar: $${\color{green}str}$$] ) |

| Call signatures                                                                                                                                                                                                                                                                     |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| print_line()                                                                                                                                                                                                                                                                        |
| print_line( printer: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), [delimiter: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term)], [quotechar: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term)] ) |

| Purpose    | Value                         |
|:-----------|:------------------------------|
| Main focus | print_line() is a side-effect |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


