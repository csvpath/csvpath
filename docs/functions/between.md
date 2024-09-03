
# Between

The functions to compare the ordering of three values are:

- `between()` or `inside()` to check if a value is between two other values
- `beyond()` or `outside()` to check if a value is not between two other values

These comparisons can be done using just the `above()` and `below()` functions; however, that is much less concise. There is no significant difference in the functionality. The order of the two comparison value is not important.

`inside()` and `outside()` are just aliases that may feel like the right terms for certain use cases.

## Examples

```bash
    $[*][ between(#graduation, 2003, 2023) ]
```
This path checks if the year of graduation is within a twenty year period.

```bash
    $[*][ between(@gradulation, date("2020-05-30", "%Y-%m-%d"), date("2000-05-30", "%Y-%m-%d"))]

This path does a similar test using date objects.
