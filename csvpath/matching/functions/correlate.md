
# Correlate

Correlate calculates the correlation between two columns of numbers. It takes each column as a list of floats.If a row does not have a value in either of the columns, the tuple is captured to a `correlate_gap` variable with the row number as tracking key. The result of correlate is updated for each row seen.

The correlation value is given in a tuple with related data:
- The line number
- Variance left
- Variance right
- The covariance
- The correlation

The running track of the column values needed for the calculations is stored as a list of float in `correlate_left` and `correlate_right`.

Correlate takes `onmatch` and can have a name qualifier to set the key names of its data. For e.g. using:

    [ correlate.cor(#0, #1) ]

You would have variables:
- cor_left
- cor_right
- cor_gap
- cor

## Example

    $file.csv[1*][ correlate.cor(#years, #salary) ]

This path gives a correlation of experience to salary.


