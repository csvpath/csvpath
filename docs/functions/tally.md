
# Tally

Tracks the value of a variable, function, or header. Tally always matches. It also collects its tally regardless of other matches or failures to match, unless you add the `onmatch` qualifier.

Tally keeps its count in variables named for the values it is tracking. A header would be tracked under its name, prefixed by `tally_`, as:

    {'tally_firstname': {'Fred':3}}

Tally can track multiple values. Each of the values becomes a variable under its own name.

Tally also tracks the concatenation of the multiple values under the key `tally`. To use another key name add a non-keyword qualifier to tally. E.g. `tally.birds(#bird_color, #bird_name)` has a tally variable of `birds` with values like `blue|bluebird`,`red|redbird`.

## Examples

    $file.csv[*][tally(#lastname)]

This path creates a  `tally_lastname` variable like:

    {'tally_lastname': {'Kermet': 1, 'Smith':3}}

Multiple values can be used as arguments to tally().

    $file.csv[*][tally(#firstname, #lastname)]

This path creates variables for firstname and lastname. In addition it creates a variable named `tally` that holds the concatenation of the values, pipe delimited. The set of variables are like:

    {
        'tally_firstname': {'David': 3, 'Bob':5},
        'tally_lastname':{'Jones':2, 'Smith':5},
        'tally':{'David|Jones':1, 'Bob|Smith':1, ...
    }

To limit tally to only matching rows use the `onmatch` qualifier like this:

    $file.csv[*][
        or( #firstname == "Frog", #firstname == "Ants" )
        tally.my_tally.onmatch(#firstname, #lastname)
    ]

Which would result in variables like these:

    {
      'my_tally_firstname': {'Frog': 2, 'Ants': 1},
      'my_tally_lastname': {'Bat': 3},
      'my_tally': {'Frog|Bat': 2, 'Ants|Bat': 1}
    }

