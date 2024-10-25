
# Variables

Variables are identified by an `@` followed by a name. A variable is set or tested depending on the usage. When used as the left hand side of an `=` its value is set.  When it is used on either side of an `==` it is an equality test.

## Overview

- [Tracking Values](#tracking)
- [Qualifiers](#qualifiers)
- [Assignment](#assignment)
- [Naming](#naming)
- [Printing](#printing)
- [Sharing Variables Between CsvPath Instances](#sharing)
- [Examples](#examples)

<a name="tracking"></a>
## Tracking Values

Variables may have "tracking values". A tracking value is a key into a dict stored as the variable. Tracked values are often used by functions for internal bookkeeping. A csvpath can get or set a tracking value by using a qualifier on the variable name. E.g.

```bash
    @name.a_name = #firstname
```

The tracking value qualifier must not match any of the predefined qualifiers, like `asbool` or `onmatch`. As usual, the order and number of qualifiers is not important.

Note that a variable's name and tracking value are strings. If you request a variable with a boolean tracking value that looks like `@empty.True`, the value will nevertheless be found. This often happens when using `count()` or another bool producing function.

<a name="qualifiers"></a>
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

### Latch

`latch` offers the ability to set a variable one time and have it not change thereafter. When a variable has `latch` it sets once and returns the default match result. After that, `latch` disallows changes to the variable but still returns the default match value, thereby not blocking the line from matching.

### Increase and Decrease

`increase` and `decrease` prevent variables from being set to values that are less than or greater than, respectively, the variable's current value. For example, a variable with the `increase` qualifier that has the value `10` cannot be set to `9` but can be set to `11`. `increase` and `decrease` affect a line matching or not matching. If a variable change is prevented because it goes in the opposite way permitted by the qualifier it prevents the line matching. As always, this effect can be removed by adding the `nocontrib` qualifier in addition to `increase` or `decrease`.

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/qualifiers.md'>Read about these qualifiers and more here.</a>

<a name="assignment"></a>
## Assignment

Variables are assigned on the left-hand side of an `=` expression. For example:

- `@name = #firstname`
- `@time.onchange = gt(3, @hour)`

At present, a variable assignment of an equality test is not possible using `==`. In the future the csvpath grammar may be improved to address this gap. In the interim, use the `equals(value,value)` function. I.e.instead of
    @test = @cat == @hat
use
    @test = equals(@cat, @hat)

A variable can be assigned early in the match part of a path and used later in that same path on the same line. Both the assignment and use are in the context of the same line in the CSV file so each change in the variable changes the value for subsequent uses. For e.g.

    [@a=#b #c==@a]

Can also be written as:

    [#c==#b]

Variables are always set unless they are flagged with the `.onmatch` or another qualifier described above. That means:

    $file.csv[*][ @imcounting.onmatch = count_lines() no()]

will never set `imcounting`, because of the `no()` function disallowing any matches, but:

    $file.csv[*][ @imcounting = count_lines() no()]

will always set it.

Read <a href='https://github.com/dk107dk/csvpath/blob/main/docs/assignment.md'>more about qualifiers and variable assignment here</a>.

<a name="naming"></a>
## Naming

Variable names are relatively restrictive. The CsvPath grammar currently defines variable names to match:

```regex
    /@[a-zA-Z-0-9\_\.]+/
```

A.k.a., one or more letters, numbers, underscores, and dots. Additionally, a variable name cannot begin with a period.

<a name="printing"></a>
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

<a name="sharing"></a>
## Sharing Variables Between CsvPath Instances

Using a CsvPaths instance you can setup and coordinate the action of multiple CsvPath instances. While there is no shared variable space across the CsvPath instances being managed by a CsvPaths instance, the set of CsvPath instances can access each other's variables using references.

Each CsvPath instance in the set of instances has read-only access to the state of the other CsvPath instances. This access allows signaling and coordination between them. The federated variables are namespaced by the name of the set of CsvPath instances, their named-paths (and/or identical named-results) name. Since the namespace is federated under one named-paths name, changes made by a csvpath are local to its CsvPath instance but effectively overwrite any same-name variable that is run before. From a reference's point of view, two variables with the same name, each in its own csvpath run by a separate CsvPath instance, are the same variable.

For example, consider a named-paths set of csvpaths called `sharing_example` that has this form:

```bash
    ~ id: day-one ~
    $[*][ @first_day = "Monday" ]

    ---- CSVPATH ----
    ~ id: day-two ~
    $[*][ @second_day = "Tuesday" ]
```

We can add a third csvpath that references the first two like this:

```bash
    ~ id: day-one ~
    $[*][ @first_day = "Monday" ]

    ---- CSVPATH ----
    ~ id: day-two ~
    $[*][ @second_day = "Tuesday" ]

    ---- CSVPATH ----
    ~ id: schedule ~
    $[*][
        print("
            Schedule
            ---------
            $sharing_example.variables.first_day: Introductions and opening remarks
            $sharing_example.variables.second_day: Presentations and workgroup sessions
        "
    ]
```

It is, of course, also possible to create references to other named-paths variables from other groups of csvpaths run by different CsvPath instances managed by a different CsvPaths instance.

<a name="examples"></a>
# Examples
- `@weather="cloudy"`
- `count(@weather=="sunny")`
- `#summer==@weather`
- `@happy.onchange=#weather`

The first is an assignment that sets the variable and returns True.

The second is an argument used as a test in a way that is specific to the function.

Number three is a test.

Number four sets the `happy` variable to the value of the `weather` header and fails the row matching until `happy`'s value changes.



