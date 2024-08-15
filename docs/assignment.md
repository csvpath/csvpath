
# The Role Of Qualifiers In Assignment

Assignment is the process of setting a variable equal to a value from another variable or a header, function, or term. There is more to assignment than you might think.

Assignments have this common `x = y` form:

- `@x = #y`
- `@x = "a value"`
- `@x = @y`
- `@x = count()`

Where things get more interesting is qualifiers.

There are a number of qualifiers. These are the ones that are involved with assignment:

- `asbool`
- `onchange`
- `onmatch`
- `nocontrib`
- `latch`

You can <a href='https://github.com/dk107dk/csvpath/blob/main/docs/qualifiers.md'>read about them here</a>.

Qualifiers can go together in any order. CsvPath decides what to do in an assignment based on all the qualifiers that it finds and which are applicable. There are three ways a qualifier relates to an assignment:

- It may qualify the specific act of the assignment
- It may qualify the assignment's relationship to the whole row
- Or it can apply to just the actual value itself that is being assigned

You can think of these happening in layers.

## Match Values Of Assignments

| Form                                               | Match value                                |
|----------------------------------------------------|--------------------------------------------|
| `@x = y`                                           | True                                       |
| `@x.latch = y`                                     | True                                       |
| `@x.onchange = y`                                  | if changed True otherwise False            |
| `@x.onmatch = y`                                   | if row matches True otherwise False        |
| `@x.[any-qualifiers-except-nocontrib].asbool = y`  | True or False determined by the value of x |
| `@x.[any-other-qualifiers].nocontrib = y`          | True

A typical assignment contributes `True` to the csvpath's match for a row. Likewise, latched and onchange assignments contribute to a match. One way to think about this is that returning True to indicate a match is basically saying that the assignment doesn't matter for matching.

A latched assignment is one where the variable is set once and then never changes. For any row, regardless if the latched variable has been set, the match value is True. Again, the idea is that the latched assignment is a non-consideration for matching.

An `onchange` assignment is one that only happens when the variable's value changes. Obviously, if a variable's value is the same as as the new value it doesn't matter for that variable if the assignment happens. However, `onchange`'s effect is on the match, not the assignment. If a variable with `onchange` is assigned to a value that it already holds, the match fails for the whole row. Conversely, if the same variable is given a new value, the variable's contribution to the row matching is True.

`onmatch` is similar. If a row matches in all other respects, its `onmatch` variable assignments happen. If the same row doesn't match in other respects, the `onmatch`ed variable concurs -- it doesn't make the assignment and returns False in the match.

`asbool` overrides the previously described variable qualifiers. If `asbool` is found, the assignment returns True or False in the match according to the value the variable is set to. The interpretation of the variable's new value as a bool is similar to Python's `bool(x)`, but with the addition of "true" and "false" being treated as the True and False value, respectively.

Finally, `nocontrib` is superior to all the other variable qualifiers. If found, the match returns True. It is, again, a way of taking the assignment out of consideration for the match.

The primacy or order of consideration is:

1. No qualifiers
2. `nocontrib` overrides all below, making any other qualifiers meaningless
3. `asbool` overlays all below, after any changes
4. `onchange` or `latch` without `onmatch` are considered before any combinations that include `onmatch`
5. `onmatch` plus `onchange` and/or `latch` is considered before just `onmatch`
6. `onmatch`

This may seem like a lot. And it is. The silver lining is that the qualifiers have a lot of expressive power that you can tap into when you need it, and ignore when you don't.


