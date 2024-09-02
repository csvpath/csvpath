
# Increment

Returns an increment counter that is updated each time a value is seen N times. Increment takes a value in its first argument. Its second argument is an integer indicating how many times the first argument must match before the function's increment counter ticks up by one.

Internally the increment function has two counters: a match counter and an increment counter.

The match counter is increased by 1 every match. The increment counter updates by 1 only when the match counter mod the increment size is zero. I.e.:

    match_counter % n == 0

By default, the match counter is available in the path variables as 'increment' and the increment counter is 'increment_increment'. To set a more helpful name, use a qualifier on the function name. E.g.:

    @i = increment.index( yes(), 3)

This path would result in variables like:

    {'i': 3.0, 'index': 9, 'index_increment': 3.0}

To make the match depend on the whole row, in addition to the increment function's own match value, use the onmatch qualifier. E.g.

    @i = increment.index.onmatch( yes(), 3 )

## Example

This path explicitly collects three variables and creates 9 total variables.

    $file.csv[*]
            [
                @i = increment.test( yes(), 3)
                @j = increment.double_check( yes(), 2)
                @k = increment.rand( random(0,1) == 1, 2)
            ]

The 9 variables are:
- i
- j
- k
- test
- test_increment
- double_check
- double_check_increment
- rand
- rand_increment

This path:

    $file.csv[*]
            [
                @i = increment.never.onmatch(yes(), 3)
                @j = increment.always(yes(), 3)
                no()
            ]

Creates variables like:

    {'never': None, 'i': 0, 'always': 9, 'j': 3.0, 'always_increment': 3.0, 'never_increment': None}
