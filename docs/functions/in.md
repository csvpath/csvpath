
# In

`in()` compares its first argument to all the other arguments, returning a match if arg one is equal to any of the others.

The first argument can be any match component except assignments and when/do statements.

The following arguments can be likewise. Additionally, `in()` tests any arguments that are string Terms as pipe delimited lists of values. This means you can test a value against a string of pipe delimited possible matches like this:

```bash
    in(#firstname, "John|Mary|Jim|Sally")
```

This match component checks if the value of the `#firstname` header is in the list John, Mary, Jim, or Sally.

You can also test against a mixed set of value like this:

```bash
    in(#firstname, "John|Mary", #aunt, #uncle, @friends)
```

In this case the `in()` is checking if the line's `#firstname` value is either in the list [John, Mary] or is the value of the `#aunt` header or is the value of the `#uncle` header or equals the variable `@friends`.

## Examples

    $file.csv[*][in(#firstname, "Tom|Dick|Harry")]

This path matches when the value of the `firstname` column is `Tom`, `Dick`, or `Harry`.

    $file.csv[*][
                    @x.onmatch = count()
                    in(#firstname,"Bug|Bird|Ants")
    ]

This path sets `x` to the number of times the `firstname` column is `Bug`, `Bird`, or `Ants`.

    $file.csv[*][
                    @x.onmatch = count(in(#firstname,"Bug|Bird|Ants"))
                    in(#firstname,"Bug|Bird|Ants")
    ]

This path sets `x` to the number of times the `firstname` column is `Bug`, `Bird`, or `Ants`. It also sets the count variable `True` to the same number. Of the two paths, this is obviously not the better choice, but it is an interesting example.

