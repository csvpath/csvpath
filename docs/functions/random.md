
# Random and Shuffle

These two functions give you access to random numbers.

`random()` returns a random int within the range of its two required args. Both arguments must be positive ints. The first must be less than the second. `random()`'s degree of randomness is that of Python's built-in random function.

`shuffle()` gives a random number within a range for every call without replacement, i.e. no duplicates. Like `random()` the two arguments must be positive ints with the second being larger than the first.

If you call `shuffle()` twice in one csvpath you get two random numbers from the range and the range is exhausted in half the time. After the range is exhausted the return is None.

`shuffle()` can take a name qualifier so that you can use multiple shuffles in one csvpath. When you use a name qualifier your shuffle does its random number bookkeeping using a variable with that name.

`shuffle()` has a no-arguments form that uses the range 0 to last data-line number.

## Examples

```bash
    $[1*][
        replace( #id, shuffle() )
    ]
```
This csvpath replaces the `id` header value with a random int in the range 0 to last data-line number. No `id` will receive a None.

