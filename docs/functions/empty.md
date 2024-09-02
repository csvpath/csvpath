
# Empty and Exists

These functions take a value and return a result by interpretation. They are almost the inverse of each other.

## asbool

Both `empty()` and `exists()` can take the `asbool` qualifier in order to be treated as their value. `asbool` takes precedence over any other interpretation.

## empty()

If `asbool` the test is simply to cast to a `bool` using:

    bool(value)

If an exception is raised the result is `False`.

If not `asbool` the test is:
- If `None` == `True`
- If an empty `list` == `True`
- An empty `dict` == `True`
- An empty `Tuple` also == `True`
- The empty string (after applying `strip()` == `True`
- Otherwise == `False`

## exists()

`asbool` is handled the same as in `empty()`.

If not `asbool` the test is:
- If `None` == `False`
- If `nan` == `False`
- When stringified and stripped is the empty string == `False`
- Otherwise == `True`

## Example

```bash
    $file.csv[*][@existiant = exists(#age)]
```


