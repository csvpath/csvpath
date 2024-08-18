
# And and Or

`and()` and `or()` do what you would expect:
- And requires all the match components it contains to match for it to match
- Or requires just one of its contained match components to match

The whole match part of a csvpath is an ANDed string of match components. However, there are times when you need more control. The best example is using a `->` (the _when_ operator) that needs to depend on two matches, not just one.

## Examples

```bash
    $[1*][
        ~ when there are updates after the completition date or
          the work wasn't completed, invalidate ~
        or(
            above(date(#updated, "%d/%m/%Y"), date(#completed, "%d/%m/%Y"),
            empty(#completed)
        ) -> fail_and_stop()
```

```bash
    $[1*][
        tally.levels(#level)
        @logbalance = above(@level.WARN, @level.DEBUG)
        and(last(), @logbalance.asbool) -> fail()
        and(last(), @logbalance.asbool) -> print("The warning and debugging message counts are inverted")
    ]
```

