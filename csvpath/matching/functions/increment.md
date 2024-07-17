
# Increment

Returns an increment counter that is updated each time a value is seen N times. Increment takes a value in its first argument. Its second argument is an integer indicating how many times the first argument must match before the function's increment counter ticks up by one.

Internally the increment function has two counters: a match counter and an increment counter.

The match counter is increased by 1 every match. The increment counter updates by 1 only when the match counter mod the increment size is zero. I.e.:
   match_counter % n == 0

By default, the match counter is available in the path variables as 'increment' and the increment counter is 'increment.increment'. To set a more helpful name, use a qualifier on the function name. E.g.:

   @i = increment.index( yes(), 3)

This path would result in variables like:
    {'i': 3.0, 'index': 9, 'index.increment': 3.0}

## Example

    $file.csv[*]
            [
                @i = increment.test( yes(), 3)
                @j = increment.double_check( yes(), 2)
                @k = increment.rand( random(0,1) == 1, 2)
            ]




