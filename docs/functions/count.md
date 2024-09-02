
# Count

Returns the number of matches. When used alone count() gives the total matches seen up to the current line in the file.

Matches can be scoped down to a contained existence test or equality. Counting an equality means a function, term, variable, or header compared to another function, term, variable, or header.

When `count()` is scoped to its contained value, the count is of the values seen. If it is a bool, the count is of `True` and `False`. If an int, it is a count of each value seen. For e.g.

```bash
    count( empty( #zipcode ) )
```

This use of `count()` counts the number of times it sees `True` and `False`. Whereas,

```bash
    count( #zipcode )
```

Counts the number of times each value of `zipcode` is seen.

When counting the values it sees, the `count()` function stores the value-integer pairs in a variable under a key identifying the count function. The ID of the count function is a hash by default, making it difficult for a human to understand which count the key represents. To name the count use a qualifier on the count function. A qualifier is a name that follows the function name separated by a dot. E.g.:

```bash
    count.my_named_count(#0="red")
```

For example you can do do something like this:

```bash
    $file.csv [*]
              [
                 @t.onmatch=count.firstname_match(#firstname=="Ants")
                 #firstname=="Ants"
              ]
```

This path counts the number of matches of `#firstname` into the path's variables so that the variable name is like:

```bash
    {'firstname_match':{True:1}}
```

`count()` can take the `onmatch` qualifier. When there is a contained value and `onmatch`, count only increments if its contained value matches. For e.g.

```bash
    $[*][
        count.onmatch( in(#firstname,"Bug|Bird|Ants") ) == 2
    ]
```

This path counts first names that match the `in()` function. If the count equals `2` the row will also match. This is a different behavior from that of other match components in that count is using `onmatch` to look inward, rather than at its siblings. Bear in mind, `count()` without a contained value only ever increments when the row matches. In that case, `onmatch` would add nothing.

If you create two variables tracking a boolean value using `count()` the results may look counter intuitive.

```bash
    @empty = count.e( empty(#20) )
    @full = count.f( not( empty(#20) ) )
```

In this case `empty` and `full` will both be counting the value `True`. The actual value of empties and fulls can be found in either of `e` or `f` as:

```bash
    @e.True == subtract( @f.True, count_lines() )
```


