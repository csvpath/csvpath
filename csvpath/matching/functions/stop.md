
# Stop

Stops the scan immediately on a condition or by being match-activated by an enclosing function. Always returns True to matches() and to_value().


## Example

    $file.csv[*][
                    @counting=count_lines()
                    stop(@counting==5)
                ]

This contrived example path stops the scan when the line count hits 5.



