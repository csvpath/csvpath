
Track

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



| Data signatures                                                  |
|:-----------------------------------------------------------------|
| track( track under: str, tracking value: Any, ['collect': Any] ) |

| Call signatures                                                                                                                           |
|:------------------------------------------------------------------------------------------------------------------------------------------|
| track( track under: TermǁVariableǁHeaderǁFunctionǁReference, tracking value: TermǁVariableǁHeaderǁFunctionǁReference, ['collect': Term] ) |

| Purpose    | Value                    |
|:-----------|:-------------------------|
| Main focus | track() is a side-effect |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |


