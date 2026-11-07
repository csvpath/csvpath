
## metadata()

Provides access to the metadata values and settings directives that
are user-set in external comments.

A metadata key-value pair is set by a word followed by a colon. The
value is all characters up to the next word-colon key or, if none, the
end of the comment.

The metadata() function finds both mode settings (e.g. xyz-mode:) and
any arbitrary key-value pairs set by the csvpath writer. Settings
directives and user-defined key-values are handled exactly the same.

| Data signatures                            |
|:-------------------------------------------|
| metadata( [name: $${\color{green}str}$$] ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| metadata( [name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ǁ Equality] ) |

| Purpose                | Value                                  |
|:-----------------------|:---------------------------------------|
| Main focus             | metadata() produces a calculated value |
| Has internal variables | False                                  |

| Context          | Qualifier                                                                                                                                                                                                                                      |
|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch)                                                                                                                                                             |
| Value qualifiers | [tmp](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#tmp), [renew](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#renew), [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
