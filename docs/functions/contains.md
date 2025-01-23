
# contains() and find()

These functions operate on strings and take the same two string arguments:
- a string to compare
- a second string that may be contained by the first

`contains()` is the same as the Python `s in s2`, where `s` and `s2` are any strings. With `contains()`, if the second string is contained by the first the return is `True`; otherwise, `False`.

`find()` returns the index where the second string starts within the first. If the second string is not contained within the first string the result is -1.

Both functions handle `none()` or `None` by returning False or -1.

## Example

```bash
    $file.csv[1*][
        @string = "It was the best of times"
        @find = "today"
        @c = contains(@string, @find)
    ]
```

In this path `@c` is `False` because `@find` does not occur in `@string`.


