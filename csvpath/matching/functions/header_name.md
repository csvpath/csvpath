
# Header Name and Header Index

`header_name()` and `header_index()` have two functions:
- They look up names by index number and numbers by name
- They indicate if the name or number found matches the expected name or number

If you give `header_name()` and integer it will find the name of that header. Remember that header indexes are 0-based. If the lookup fails the value result is `None`. The match result is `False`.

If you also provide `header_name()` a second string argument that is the expected name, it will return `True` if the names match; otherwise, `False`.

`header_index()` does the same, but with a name to look up and, optionally, an expected index value.


## Examples

```bash
    $[*][
        @firstname_index = header_name("firstname")
        @firstname_index_is_correct = header_name("firstname", 0)
    ]
```
This path looks for the index of `#firstname` and, if found, sets the `@firstname_index` variable. It also does the same lookup but with an expected value, `0`. If the expected value matches the actual index of `#firstname`, `@firstname_index_is_correct` will be set to `True`.

