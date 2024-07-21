
# Stop

Stops the scan immediately on a condition or by being match-activated by an enclosing function. Always returns True to matches() and to_value().


## Example

    $file.csv[*][
                    @counting=count()
                    stop(@counting==5)
                ]

This path stops the scan when the match count hits 5.

    $file.csv[*][ when(
                    above(
                        count(),
                        5),
                    stop())
                ]

This path stops scanning if its match count goes above 5.

