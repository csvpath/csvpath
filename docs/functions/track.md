
# Track

`track()` sets a variable with a tracking value that matches another value. The name of the variable is either `track` or a non-reserved qualifier on the function.

For example:

```bash
    $[*][
         track.my_cities(#city, #zip) ]
```

This path creates a variable called `my_cities`. Within that variable each city name will track a zip code. This is a dictionary structure so under the covers you might have:

```python
    my_cities["Boston"] == 02134
```

Track can take the `onmatch` qualifier. If `onmatch` is set and the row doesn't match `track()` does not set the tracking variable; however, it does still return true. That is to say, `track()` doesn't have an effect on a row matching.

## Examples

```bash
    $[*][ track(@weekdays, #day_of_game)
        @track.Monday == "rain" -> stop()
    ]
```

This csvpath says that the CSV file processing should stop if a Monday game was rained out.



