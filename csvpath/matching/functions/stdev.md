
# Stdev and Pstdev

These functions take the standard deviation for a list of numbers that represent a sample or a population, respectively.


## Example

```bash
    $file.csv[1*][
        above(#years, 5)
        push("years", #years)
        @running_std = stdev.onmatch(stack("years"))
    ]
```

This path gives a running stdev of years of experience in a sample of people with more than 5 years on the job.

```bash
    $test[1*][
        @r = random(0,1)
        @r == 1 -> push("years", #years)
        last.nocontrib() -> @std = stdev("years")
        last.nocontrib() -> print("The sample set stdev of years on the job is $.variables.std")
    ]
```

At the end of scanning a file this path prints the standard deviation of the years of experience of a random sample of the population.



