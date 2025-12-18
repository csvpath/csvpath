
## track()

track() sets a variable with a tracking value that matches another
value. The name of the variable is either track or a non-reserved
qualifier on the function.

For example:

$[*][ track.my_cities(#city, #zip) ]

This path creates a variable called my_cities. Within that variable
each city name will track a zip code. This is a dictionary structure.
If no name qualifier is present the variable name is 'track'.

Behind-the-sceens the tracking data structure is like:

my_cities["Washington"] == 20521

track() can take the onmatch qualifier. If onmatch is set and the row
doesn't match, track() does not set the tracking variable

track() is a side-effect with no effect on a row matching.

track() can take a third argument, 'collect'. If 'collect' is passed
the tracked values are pushed on a stack variable. No third argument
results in the tracked value being replaced at every line.



Note that track() treats all values as strings; whereas, track_any()
attempts to convert values. In the zip code example track_any() would
not capture leading zeros, but track() would.



| Data signatures                                                                                                           |
|:--------------------------------------------------------------------------------------------------------------------------|
| track( track under: $${\color{green}str}$$, tracking value: $${\color{green}Any}$$, ['collect': $${\color{green}Any}$$] ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| track( track under: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), tracking value: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), ['collect': [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term)] ) |

| Purpose    | Value                    |
|:-----------|:-------------------------|
| Main focus | track() is a side-effect |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Name qualifier   | optionally expected                                                                |


