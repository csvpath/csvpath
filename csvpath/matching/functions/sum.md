
# Sum

`sum()` keeps a running summation of a column or other numeric value.

By default `sum()` tracks its value in the variable `sum`. Add a qualifier to use another name.

`sum()` can take `onmatch`.

## Examples

Sum is a convenience, not a necessity. You can achieve the same result just adding a variable to itself.

```bash
    ${PATH}[1*][
                          sum(#0)
                @notsum = add( @notsum, #0)
            ]
```

You save a few keys with `sum()`. The ability to use `onmatch` on the function, rather than on the variable, is also nice.

```bash
    $[1*][
        #direction == "inbound"
        sum.calls_received.onmatch(#"calls per day")
    ]
```

This csvpath increases the `calls_received` variable by the number of calls seen in a day. It is equivalent to:

```bash
    $[1*][
        #direction == "inbound"
        @calls_received.onmatch = add( @calls_received, #"calls per day") )
```


