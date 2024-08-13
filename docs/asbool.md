
# Asbool

The `asbool` qualifier makes the match component it is used on be considered as a bool according to its value, rather than as an existence test.

The difference is:

- CsvPath evaluates "true" and "false" as their bool equivalents, True and False respectively
- A match component used as an existence test without `asbool` evaluates to True or False based on any its `not None` condition, resulting in, for e.g., the value `False` == `True` because it exists

As an example, the value of `not.asbool()` is assigned according to:

| When                                        | Example             | Example's result    |
|---------------------------------------------|---------------------|---------------------|
| If used alone, as a boolean match condition | #a                  | evaluated as a bool |
| Assignment                                  | @a = #b             | True                |
| With the `nocontrib` qualifier              | @a.nocontrib = no() | True                |
| With the `onchange` qualifier               | @a.onchange = @b    | True                |
| With the `latch` qualifier                  | @a.latch = @b       | True                |
| With the `onmatch` qualifier                | @a.onmatch = @b     | True for the purposes of the whole row matching and evaluated as a bool if/when it does |


