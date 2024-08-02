
# Variables

Variables are identified by an @ followed by a name. A variable is set or tested depending on the usage. When used as the left hand side of an "=" its value is set.  When it is used on either side of an "==" it is an equality test.

Variables may have "tracking values". A tracking value is a key into a dict stored as the variable. Tracked values are often used by functions for internal bookkeeping. A csvpath can get or set a tracking value by using a qualifier on the variable name. E.g. `@my_var.my_tracked_value`. The qualifier must not match any of the predefined qualifiers, like `asbool` or `onmatch`. As usual, the order and number of qualifiers is not important.

Variables can take an `onmatch` qualifier to indicate that the variable should only be set when the row matches all parts of the path.

A variable can also take an `onchange` qualifier to make its assignment only match when its value changes. In the usual case, a variable assignment always matches, making it not a factor in the row's matching or not matching. With `onchange` the assignment can determine if the row fails to match the csvpath.

Note that at present a variable assignment of an equality test is not possible using `==`. In the future the csvpath grammar may be improved to address this gap. In the interim, use the `equals(value,value)` function. I.e.instead of
    @test = @cat == @hat
use
    @test = equals(@cat, @hat)

# Examples
- `@weather="cloudy"`
- `count(@weather=="sunny")`
- `#summer==@weather`
- `@happy.onchange=#weather`

The first is an assignment that sets the variable and returns True.

The second is an argument used as a test in a way that is specific to the function.

Number three is a test.

Number four sets the `happy` variable to the value of the `weather` header and fails the row matching until `happy`'s value changes.



