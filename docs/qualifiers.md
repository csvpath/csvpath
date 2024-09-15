
# Qualifiers

Variables, headers, and functions can take qualifiers on their names. A qualifier takes the form of a dot plus a qualification name. Qualifiers look like:

```bash
    [ @myvar.onmatch = yes() ]
```

Or:

```bash
    [ @i = increment.this_is_my_increment.onmatch(yes(), 3) ]
```

When multiple qualifiers are used, order is not important.

Qualifiers can have a large impact in variable assignments. Read  <a href='https://github.com/dk107dk/csvpath/blob/main/docs/assignment.md'>more about qualifiers and variable assignment here</a>.

Qualifiers are relatively new and are being added opportunistically. Not all functions support all the qualifiers that might seem to be applicable. See the individual function docs for which qualifiers are available on each function.


## Well-known Qualifiers
At the moment there are only a few "official" qualifiers that are broadly available.

- `asbool`
- `decrease`
- `increase`
- `latch`
- `nocontrib`
- `notnone`
- `once`
- `onchange`
- `onmatch`

### asbool
When `asbool` is set on a variable or header its value is interpreted as a bool rather than just a simple `is not None` test

|Functions | Headers | Variables |
|----------|---------|-----------|
| No       | Yes     | Yes       |

Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/asbool.md'>more about asbool here</a>.

### increase and decrease
Adding `increase` to a variable makes the variable only set when it would go up in value. The first value set, when the current value is None, always works. Attempts to update the variable with a lower value do nothing, other than return False for matching. Setting `nocontrib` allows `increase` to function as a guard on the value without impacting the overall line match.

`decrease` works exactly the same way, other than blocking increases in value. `decrease` always allows the first set, when the current value is None.

|Functions | Headers | Variables |
|----------|---------|-----------|
| No       | No      | Yes       |


### latch
Adding `latch` to a variable makes the variable only set one time. The variable "latches" or locks on the first value. Subsequent attempts to update the variable do nothing, give no error or warning, and return `True` for matching, in order to not affect other components' matching.

|Functions | Headers | Variables |
|----------|---------|-----------|
| No       | No      | Yes       |

### nocontrib
`nocontrib` is set on the left hand side of a `->` to indicate that there should be no impact on the row match. E.g. `$test[*][yes() last.nocontrib() -> print("last line!")]` will collect all rows but only print on the last; whereas, without `nocontrib` only the last line would be collected.

|Functions | Headers | Variables |
|----------|---------|-----------|
| Yes      | No      | No        |

### notnone
`notnone` is set on a variable in an assignment to indicate that the assignment should only happen if the value being assigned is not None.

|Functions | Headers | Variables |
|----------|---------|-----------|
| No       | No      | Yes       |

### once
Add `once` to a function to indicate that it should fire at most one time. `once` is the function equivalent of variables' `latch`.

|Functions | Headers | Variables |
|----------|---------|-----------|
| Yes      | No      | No        |


### onchange
Add `onchange` to a variable to indicate that a row should only match when the variable is set to a new value.

|Functions | Headers | Variables |
|----------|---------|-----------|
| No       | No      | Yes       |

### onmatch
`onmatch` indicates that action on the variable or function only happens when the whole path matches a row.

|Functions | Headers | Variables |
|----------|---------|-----------|
| Yes      | No      | Yes       |

## Arbitrary Names
You can also add an arbitrary string to a function name or a variable.

When used with functions, this additional name is for the function's internal use, typically to name a variable.

As an example, the `tally()` function sets an internal variable under the key `tally`. This variable would be overwritten if you used two `tally()` functions in one csvpath. Adding a name qualifier fixes that problem:

```bash
    $test[*][ tally.my_tally(#firstname) tally.my_other_tally(#lastname)]
```

When an arbitrary string qualifier is added to a variable name it is treated as a tracking value. A tracking value is used to turn a variable into a dictionary of tracked values. For e.g.

```bash
    $test[1][ @friend.firstname = #firstname @friend.lastname = #lastname ]
```

This path creates a `friend` variable as a dictionary. The `friend` dictionary has `firstname` and `lastname` keys. The value of the keys are set to the corresponding header value.



