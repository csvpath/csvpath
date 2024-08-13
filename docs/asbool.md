
# Asbool

The `asbool` qualifier makes CsvPath consider the match component it is used on as a bool according to its value, rather than as an existence test.

The difference is:

- CsvPath evaluates "true" and "false" as their bool equivalents, `True` and `False` respectively
- A match component used as an existence test without `asbool` evaluates to `True` or `False` based on any its `not None` condition, resulting in, for e.g., the value `False` == `True` because `False` exists

As an example, the value of `not.asbool()` is assigned according to:

| When                                        | Example             | Example's result    |
|---------------------------------------------|---------------------|---------------------|
| If used alone, as a boolean match condition | #a.asbool           | evaluated as a bool |
| Assignment                                  | @a.asbool = #b      | True                |
| With the `nocontrib` qualifier              | @a.nocontrib.asbool = no() | True. In this case `nocontrib` overrides the match value of `asbool`. |
| With the `onchange` qualifier               | @a.onchange.asbool = @b | evaluated as a bool |
| With the `latch` qualifier                  | @a.latch.asbool = @b| evaluated as a bool |
| With the `onmatch` qualifier                | @a.onmatch.asbool = @b     | True for the purposes of the whole row matching and evaluated as a bool if/when it does |


