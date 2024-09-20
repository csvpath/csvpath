
# Push, Pop, Peek

This family of functions allows you to create list variables.

| Function       | Description                                  | Arguments     | Returns       |
|----------------|----------------------------------------------|---------------|---------------|
| `push`         | Pushes values on the top of the list         | name, value   | True          |
| `push_distinct`| Pushes values on the list if not already present | name, value | True        |
| `pop`          | Pops values off the list LIFO                | name          | value or None |
| `peek`         | Gets the value at an index of the list       | name, int     | value or None |
| `peek_size`    | Returns the size of the list                 | name          | int           |
| `stack`        | Returns the list                             | name          | a list        |

Push can be called in the form `push_distinct()` or it can take a `distinct` qualifier. (The `distinct` qualifier may become well-known, but at the moment is ad hoc just for `push()`).

Push can also take a `notnone` qualifier. When `notnone` is set `push()` will not add an empty value to the stack. It will also not match lines while the stack is empty.

`peek()` will return None if you attempt to peek an index that doesn't exist. Likewise Popping when there is nothing on the list to pop returns None.

Peek and Pop can take the `asbool` qualifier in order to make their match depend on interpreting the value returned as a bool.

`stack(name)` will return `[]` or `[var]` rather than `None` or `var`.

## Examples

```bash
    ${PATH}[*]
    [
        ~ count the individual families in town ~
        push.distinct("families", #lastname )

        ~ what was the second family? ~
        @second_arrival = peek("families", 1)

        ~ how big is the town in terms of families? ~
        @town = peek_size("families")

        ~ if town gets too big some people move away ~
        gt(@town, 40) -> pop("families")
    ]
```


