
# All and Missing

These inverse functions are existence tests for all headers, all variables, or any subset of values.

All comes in the following forms:

<table>
<tr><th> Form     </th><th>Function                       </th></tr>
<tr><td> all()    </td><td>True if all headers contain data     </td></tr>
<tr><td> all(headers()|variables())</td><td> True if all of the values (headers, variables, functions, terms) contain data  </td></tr>
<tr><td> all(value, value, ...)</td><td> True if all of the values (headers, variables, functions, terms) contain data  </td></tr>
</table>

`missing()` has the same form and the inverse results.

When calling either function the number of headers and row columns must be equal. All of the headers must have values in the current row. An item of data is considered present when:

- It is not the empty string after whitespace is trimmed off
- It does not evaluate to None (a header would not, but a variable might)

Every other item of data is considered present.

Both functions can take the `onmatch` qualifier.

## Examples

```bash
    [ @a.asbool = all() ]
```

This csvpath matches when `all()` returns True. The row match depends on `all()`'s result because the variable being assigned has the `asbool` qualifier. Without the `asbool` the assignment would allow the row to match, regardless of the value `a` is set to.

```bash
    [ all(#firstname, #middlename, #lastname) ]
```

This path matches when a row has values under all of the headers indicated.

