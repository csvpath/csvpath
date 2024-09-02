
# Average

This function tells us the average of a value up to the current row.

The values seen that will be averaged are tracked by a count under the average variable. The count key can be the line number, the scan count, or the match count. Choice of key does not affect the average.

Average can have an `onmatch` qualifier to limit the average to matched rows. You could use line numbers as the count keys while still having only matches included in the average.

Average can take an arbitrary qualifier to name its tracking variable. This will be necessary if you want to take the average of multiple values because otherwise the two average() will both write to the `average` variable.

The median function works essentially the same as average().


## Example

    $file.csv[*][@ave = average.average_age(#age, "scan")]

This path collects ages in the `average_age` variable under scan count keys and assigns the average to the `ave` variable.


