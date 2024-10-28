
# Line

The `line()` function is the core tool for structural validation. It gives you a way to declare the data-shape of a line. `line()` is similar to the `TABLE` declaration in SQL's DDL.

`line()` takes any number of functions as arguments. The only allowed functions are data primatives. They include:
- `string()`
- `int()`
- `float()`
- `num()`
- `date()`
- `datetime()`
- `bool()`
- `none()`
- `blank()`

All of these type functions can have a `notnone` qualifier. `string()` can optionally take max and min arguments. `none()` requires an empty header. `blank()` indicates an unspecified header.

The type functions only take headers as children, with the exception of string, which also optionally takes max and min int arguments. No other functions are allowed.

The order of the type functions determines what order of headers is valid. You can think of line as being like a specialized `all()` with a defined order and the ability to accept None values, when so declared.

# Examples

```bash
    ~ name: structural validation example with two rules
      return-mode: no-matches
      logic-mode: AND
      validation-mode: print, fail, no-raise
    ~
    $[*][
        line(
            string.notnone(#firstname, 20, 1),
            string        (#middlename, 20),
            string.notnone(#lastname, 30, 2),
            int           (#age),
            date          (#date_of_birth),
            string        (#country),
            string        (#email, 30)
        )
        or( exists(#age), exists(#date_of_birth) )
        #email -> regex(#email, "@")
    ]
```

This csvpath defines a line as having seven headers that have string, int, and date typed-values. Additionally, there are two simple rules applied essentially on top of this line definition:
- A line must have either an age or a date of birth
- An email must have an `@` sign.

Because `return-mode` is set to `no-matches`, if a line doesn't match this description it will be returned as we iterate through the CSV file.

```bash
    ~ name: line definition with gaps ~
    $[*][
        line(
            string.notnone(#firstname, 20, 1),
            none(),
            string.notnone(#lastname, 30, 2),
            int           (#age),
            date          (#date_of_birth),
            blank(),
            string        (#email, 30),
            unspecified   (#widget)
        )
        ~ there is a #widget header. we don't know what it is but sometimes
          it has values. the blank() makes a placeholder for a header that
          comes after date. there is always a header there but the name
          isn't consistent ~
    ]
```

In this version we are saying that middle name is always None, after date_of_birth there is something that we don't have information about, cannot rely on, and should ignore. And that the last column will be consistently present as `#widget`, but is also unknown.


