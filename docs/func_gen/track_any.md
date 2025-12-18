
Track any
track_any() sets a variable with a tracking value that matches another
value. The name of the variable is either track or a non-reserved
qualifier on the function.

For example:

$[*][ track_any.my_cities(#city, #zip) ]

This path creates a variable called my_cities. Within that variable
each city name will track a zip code. This is a dictionary structure.
If no name qualifier is present the variable name is 'track'.

Behind-the-sceens the tracking data structure is like:

my_cities["Washington"] == 20521

track_any() can take the onmatch qualifier. If onmatch is set and the
row doesn't match, track_any() does not set the tracking variable

track_any() is a side-effect with no effect on a row matching.

track_any() can take a third argument, either 'add' or 'collect'. If
'collect' is passed the tracked values are pushed on a stack variable.
No third argument results in the tracked value being replaced at every
line.

If 'add' is passed, the header values indicated by the second argument
are added.

Note that track() treats all values as strings; whereas, track_any()
attempts to convert values. In the zip code example track_any() would
not capture leading zeros, but track() would.



| Data signatures                                                               |
|:------------------------------------------------------------------------------|
| track_any( track under: [36m[3mstr[0m, tracking value: [36m[3mAny[0m, ['collect' or 'add': [36m[3mAny[0m] ) |

| Call signatures                                                                                                                                        |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------|
| track_any( track under: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, tracking value: [36m[3mTerm[0m|[36m[3mVariable[0m|[36m[3mHeader[0m|[36m[3mFunction[0m|[36m[3mReference[0m, ['collect' or 'add': [36m[3mTerm[0m] ) |

| Purpose    | Value                        |
|:-----------|:-----------------------------|
| Main focus | track_any() is a side-effect |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | [36m[3monmatch[0m             |
| Value qualifiers | [36m[3monmatch[0m             |
| Name qualifier   | [36m[3moptionally expected[0m |


