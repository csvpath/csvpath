
# Variables

Variables are identified by an `@` followed by a name. A variable is set or tested depending on the usage. When used as the left hand side of an `=` its value is set.  When it is used on either side of an `==` it is an equality test.

## Tracking Values

Variables may have "tracking values". A tracking value is a key into a dict stored as the variable. Tracked values are often used by functions for internal bookkeeping. A csvpath can get or set a tracking value by using a qualifier on the variable name. E.g.

```bash
    @name.a_name = #firstname
```

The tracking value qualifier must not match any of the predefined qualifiers, like `asbool` or `onmatch`. As usual, the order and number of qualifiers is not important.

Note that a variable's name and tracking value are strings. If you request a variable with a boolean tracking value that looks like `@empty.True`, the value will nevertheless be found. This often happens when using `count()` or another bool producing function.

## Qualifiers

Qualifiers are words appended to variable names after a dot. They modify -- or qualify -- how the variable works. The functionality of qualifiers on variables is essentially the same as for the other match components. You can <a href='https://github.com/dk107dk/csvpath/blob/main/docs/qualifiers.md'>read about qualifiers here</a>.

The action of qualifiers on their variables can be significant. That is particularly true in variable assignment. Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/assignment.md'>more about qualifiers and variable assignment here</a>. If you don't need the nuance of qualifiers, you don't need to use them.

### Onmatch
Variables can take an `onmatch` qualifier to indicate that the variable should only be set when the row matches all parts of the path.

### Onchange
A variable can also take an `onchange` qualifier to make its assignment only match when its value changes. In the usual case, a variable assignment always matches, making it not a factor in the row's matching or not matching. With `onchange` the assignment can determine if the row fails to match the csvpath.

### Asbool
A variable value can be treated as a boolean (Python bool) by using the `asbool` qualifier. Without `asbool` a variable used alone is an existence test.

Note, too, that a variable with `asbool` that is assigned a value will return matching, or not, based on interpreting the assigned value as a bool. Without the `asbool` qualifier the assignment operation always allows the row to match, regardless of the value assigned.

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/qualifiers.md'>Read about these qualifiers and more here.</a>

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

Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/assignment.md'>more about qualifiers and variable assignment here</a>.

## Naming

Variable names are relatively restrictive. The CsvPath grammar currently defines variable names to match:

```regex
    /@[a-zA-Z-0-9\_\.]+/
```

A.k.a., one or more letters, numbers, underscores, and dots. Additionally, a variable name cannot begin with a period.

## Printing

The `print()` function uses references to give you access to variables. You can <a href='https://github.com/dk107dk/csvpath/blob/main/docs/references.md'>read about references here</a>. A reference points to metadata within a csvpath or that is held by another csvpath. They look like:
```bash
    $.variables.my_var.my_tracking_value
```

There are two types of references:
- "Local" - these references are to the same csvpath the reference is made in
- "Remote" - remote reference are pointer to the results and metadata of other csvpaths

A local reference does not need a name after the `$`. Remote references require a named-result name that the CsvPaths instance can use to provide access to the data. Remote references look like:
```bash
    $mynamed_paths.variables.my_other_var.my_other_tracking_value
```

The variable references you use in `print()` can also point to indexes into stack variables. Stack variables are the list-type variables created with the `push()` function. References to stack variable indexes in print strings look like:
```bash
    $.variables.my_stack.2
```

Since stack indexes are 0-based, this reference would resolve to the third item on the stack.

# Examples
- `@weather="cloudy"`
- `count(@weather=="sunny")`
- `#summer==@weather`
- `@happy.onchange=#weather`

The first is an assignment that sets the variable and returns True.

The second is an argument used as a test in a way that is specific to the function.

Number three is a test.

Number four sets the `happy` variable to the value of the `weather` header and fails the row matching until `happy`'s value changes.



