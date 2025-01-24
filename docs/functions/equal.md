
# Equal and not equal

`equal()` tests for equality. Aliases: `equals()` and `eq()`.

Generally the `==` test is enough, but you may find a reason to use a function instead. The main case is in assignment. At least today you can not have an `==` on the right-hand-side of an assignment. In that case, rather than using `==` you must use `equal()` or `eq()`, as in this assignment that sets the `@a` variable to False.

Do not create constructions like this:

```
    @a = 1 == 0
```

Instead do:

```
    @a = eq(1,0)
```

Other than that one caveat, `==` is what you will most likely choose to use.

## not equal to and neq

The `neq()` or `not_equal_to()` function is the same as `equals()` with a `not()` around it, like: `not(eq(1,1))`.

I.e. this is `True`:

```
    neq(@b, 0) == not(eq(@b, 0))
```

Since at this time CsvPath Language does not support a `!=` operator, the `neq()` function is more common than the `eq()`.


