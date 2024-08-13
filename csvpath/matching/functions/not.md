
# Not

Negates the value it contains. `not()` takes any value, header, variable, function, or term, and inverts its boolean value.

A match component can always be interpreted as a boolean. The interpretation will be in the forms:

- An existence test
- Its boolean match condition
- The boolean value of a component carrying the `asbool` qualifier

Not is evaluated as a Python bool in most respects. In addition to that, it treats the strings "true" and "false" as their True/False bool equivalents, after lowercasing and stripping them.

The <a href='https://github.com/dk107dk/csvpath/blob/main/docs/asbool.md'>rules for the `asbool` qualifier</a> are naturally also taken into account.

## Examples

    $logs[*][ not(#exception) ]

This path matches log lines that do not have an exception

    $jira[*][ not(#complete.asbool)]

Here rows match when the `complete` column has a value that is interpreted as the boolean True or False. `"true"` would qualify and be considered True.



