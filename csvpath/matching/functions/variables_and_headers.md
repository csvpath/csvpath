
# Headers and Variables

These functions primarily signal to other functions that they should direct themselves towards the headers or variables. `all()` and `any()` are examples of functions that may need your input using `headers()` or `variables()`.

## Headers

`headers()` also has the secondary function of doing an existence test on a header by name or index. There are other options that come close to that functionality:
- `header_name()` can validate a name or look up a name by index or an index by name
- Using a header alone as a match component can do an existence test for matching
- `header_names_mismatch()` can validate that all expected headers are present and in their right places

None of those methods gives you an easy way to set a bool variable based on the existence of a header name. That functionality is in `headers()`


## Example

```bash
    $file.csv[*][@fn = headers("firstname")]
```

This path checks for the existence of the `firstname` header and assigns the result to the `@fn` variable.

```bash
    $file.csv[*][ all(headers())]
```

This path checks that all headers have values in each line.


