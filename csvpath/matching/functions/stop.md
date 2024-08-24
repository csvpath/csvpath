
# Stop and Skip

## Stop
`stop()` stops the scan immediately when:
- An inclosed value is true
- An enclosing function is true
- It is the right-hand side of a when expression (the `->` operator)

Stop always returns True to matches() and to_value().

Also see the validation functions, including `fail_and_stop()`.

`stop()` does not prevent any other csvpaths currently in progress as part of a named csvpaths set. The CsvPaths will respect the CsvPath saying it is done, but its other CsvPath instances will continue their work.

## Skip

`skip()` also stops matching, but only for a single line. When `skip()` is activated no later match components are considered and the line does not match overall. The next line in the CSV file begins its matching immediately.

Skip is different from `advance()` in that `advance()` allows the line to complete; whereas, when it is seen, `skip()` immediately stops matching on the current row and moves to the next one.

## Side Effects

Both `skip()` and `stop()` prevent side effects that would be triggered by match components after them. Match component order is important. The components always activate in the same left to right, top to bottom order. When `skip()` or `stop()` match, no more components run.

For e.g. imagine you have a `skip()` in front of a `print()`. If the skip matches, the `print()` will not happen. If the `print()` were before the `skip()` it would happen, regardless of `skip()`.

## Example

    $file.csv[*][
        @counting=count()
        stop(@counting==5)
    ]

This path stops the scan when the match count hits 5.

    $file.csv[*][
         above(count(), 5) -> stop() ]

This path stops scanning if its match count goes above 5.

