
# Has matches

`has_matches()` returns `True` when there have been previous matches. It is a convenience function, since you can achieve the same result with `count()` and other functions; although not quite as simply.

## Examples

    $people.csv[*][
        ~ Apply three rules to check if a CSV file is invalid ~
            missing(headers())
            too_long(#lastname, 30)
            not.nocontrib( header_name(0, "firstname") ) -> fail()
            has_matches.nocontrib() -> fail()
    ]

This csvpath fails a file if any of the other match components match on any line.

