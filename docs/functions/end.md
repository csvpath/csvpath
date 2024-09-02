
# End

The `end()` function gets the value of the last header.

Add an int to `end()` to access the header that is identified by the index of the last header minus the int.For e.g.:

    $test.csv[*][ @col = end(1) ]

If there are three headers, the `col` variable will be the value of the #1 header.


