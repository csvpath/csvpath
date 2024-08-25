
# Above, Below

The ordinal comparison functions have multiple aliases, but a single simple function. They are:

- `above()`, `gt()`, `after()`
- `below()`, `lt()`, `before()`

The functionality is just what you would expect: they implement the `>` and `<` operators as functions.

Above and below handle number, date, and string comparisons. At this time they don't have any settings that would refine their function for specific use cases. Comparison by the three types is attempted in this order:
- Number
- Date
- String

There are no differences between the aliases. The reason to have them is just to suit the use case. For instance, in comparing two numbers `lt()` and `gt()` may feel more right; whereas, in finding a point in time between two dates `before()` and `after()` may feel like a better fit.

## Examples

```bash
    $[*][ before(#graduation, 2003) ]
```
This path matches on year of graduation as an int.

```bash
    $[*][ before(@gradulation, date("2020-05-30", "%Y-%m-%d"))
           after(@gradulation, date("2000-05-30", "%Y-%m-%d"))]

This path uses `before()` and `after() to find if a date is between two dates.

