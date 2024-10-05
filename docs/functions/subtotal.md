
# Subtotal

`subtotal()` keeps a running summation of a column by another other value.

The arguments are a header or variable and another header or variable.

By default `subtotal()` tracks its value in the variable `subtotal`. Add a qualifier to use another name.

## Examples

```bash
    ${PATH}[1*][
     subtotal.purchases(#company, #price)
     last() -> print("customers' purchases: $.variable.purchases")
    ]
```

The printout will be like:

```json
    { "computerstores":102044, "foodstores":12289409 }
```
