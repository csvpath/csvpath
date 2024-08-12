
# Correlate

`correlate(var1, var2)` calculates the correlation between two stacks of numbers. It treats each stack as a list of floats. The result of correlate is updated for one of:
- Each row seen
- Each row matched
- When the left-hand side of a when operator (`->`) is True

The running track of the values for the calculations is stored in variables. Use `push(name, value)` to populate the variables. To find the correlation of two columns use pushes as shown below. If values are pushed that are not convertible to float they will be trimmed out along with the value at the same index in the second variable.

Correlate takes the `onmatch` qualifier.

## Example

```bash
    $file.csv[1*][
        above(#years, 5)
        push("years", #years)
        push("salary", #salary)
        @running_corr = correlate.onmatch(#years, #salary)
    ]
```

This path gives a running correlation of experience to salary where experience is greater than 5 years.

```bash
    $test[1*][
        @r = random(0,1)
        @r == 1 -> push("years", #years)
        @r == 1 -> push("salary", #salary)
        last.nocontrib() -> @c = correlate(#years, #salary)
        last.nocontrib() -> print("correlation of years to salary is $.variables.c")
    ]
```

At the end of scanning a file this path prints the correlation of the years of experience and salary of a random sample of the population.



