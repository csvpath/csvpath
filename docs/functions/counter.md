
# Counter

`counter()` lets you run a counter a bit more easily than just adding to a variable. You are of course incrementing a variable. The important thing to remember is that you must name your counters using a qualifier. If you don't the ID generated for your counter will make it tough to use.

You can pass `counter()` an integer to set the increment; otherwise, it increments by `1`.

## Examples

    $[*][ counter.my_counter() @my_counter() == 5 -> counter.fives(5) ]

This csvpath has two counters: `my_counter` and `fives`. Both are accessible at any point as regular variables.
