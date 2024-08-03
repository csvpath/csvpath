
# Variables

Variables are identified by an @ followed by a name. A variable is set or tested depending on the usage. When used as the left hand side of an "=" its value is set.  When it is used on either side of an "==" it is an equality test.

Variables may have "tracking values". A tracking value is a key into a dict stored as the variable. Tracked values are often used by functions for internal bookkeeping. A csvpath can get or set a tracking value by using a qualifier on the variable name. E.g. `@my_var.my_tracked_value`. The qualifier must not match any of the predefined qualifiers, like `asbool` or `onmatch`. As usual, the order and number of qualifiers is not important.

_Note: as of Aug 2024 there is a grammar problem that may keep variables from being used as an existence test all on their own. In that situation use the `exists()` function as a work-around until this bug is fixed. The problem should not be seen in using the when operator (`->`)._

## Qualifiers
Variables can take an `onmatch` qualifier to indicate that the variable should only be set when the row matches all parts of the path.

A variable can also take an `onchange` qualifier to make its assignment only match when its value changes. In the usual case, a variable assignment always matches, making it not a factor in the row's matching or not matching. With `onchange` the assignment can determine if the row fails to match the csvpath.

A variable value can be treated as a boolean (Python bool) by using the `asbool` qualifier. Without `asbool` a variable used alone is an existence test.

## Assignment

Variables are assigned on the left-hand side of an `=` expression. For example:

- `@name = #firstname`
- `@time.onchange = gt(3, @hour)`

At present, a variable assignment of an equality test is not possible using `==`. In the future the csvpath grammar may be improved to address this gap. In the interim, use the `equals(value,value)` function. I.e.instead of
    @test = @cat == @hat
use
    @test = equals(@cat, @hat)

A variable can be assigned early in the match part of a path and used later in that same path. The assignment and use will both be in the context of the same row in the file. For e.g.

    [@a=#b #c==@a]

Can also be written as:

    [#c==#b]

Variables are always set unless they are flagged with the `.onmatch` qualifier. That means:

    $file.csv[*][ @imcounting.onmatch = count_lines() no()]

will never set `imcounting`, because of the `no()` function disallowing any matches, but:

    $file.csv[*][ @imcounting = count_lines() no()]

will always set it.


# Examples
- `@weather="cloudy"`
- `count(@weather=="sunny")`
- `#summer==@weather`
- `@happy.onchange=#weather`

The first is an assignment that sets the variable and returns True.

The second is an argument used as a test in a way that is specific to the function.

Number three is a test.

Number four sets the `happy` variable to the value of the `weather` header and fails the row matching until `happy`'s value changes.



