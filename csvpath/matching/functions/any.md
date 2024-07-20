
# Any

Finds values in any column or variable.

Find comes in the following forms:

<table>
<tr><th> Form     </th><th>Function                       </th></tr>
<tr><td> any()  </td><td>True if any header or variable would return a value     </td></tr>
<tr><td> any(header())  </td><td> True if any header would return a value  </td></tr>
<tr><td> any(variable())  </td><td> True if any variable would return a value   </td></tr>
<tr><td> any(value)  </td><td> True if the value can be found in any header or variable  </td></tr>
<tr><td> any(header(), value)  </td><td> True if the value can be found in any header  </td></tr>
<tr><td> any(variable(), value)  </td><td> True if the value can be found in any variable</td></tr>
</table>

Any can take the `onmatch` qualifier. If `onmatch` is set and the row doesn't match any() returns False, not None.

## Examples

    $file.csv[*][any(header())]

Are any columns populated? This is the same as naming all the headers in an or().

    $file.csv[*][any(variable(), "fish")]

True if any variable has the value `fish`.

    $file.csv[*][any.onmatch(header())]

True if there are any headers when the row matches; otherwise, False.

