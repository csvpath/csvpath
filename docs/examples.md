
# Examples

These are simple examples of csvpath match parts. Test them yourself before relying on them. See the unit test for more simple path ideas.

1. Find a value

```bash
    [ ~A running average of ages from 5 and 85~
        between(#age, 4, 86)
        @average_age.onmatch = average(#age, "match")
        last.nocontrib() -> print("The average age between 5 and 85 is $.variables.average_age")
    ]
```

2. Create a file

```bash
    [ ~Create a new CSV file sampling sales greater than $2000 in a region~
        #region == or( "emea", "us" )
        @r = random(0,1)
        @line = line_count()
        gt(#sale, 2000)
        @ave = average.test.onmatch(#sale, "line")

        count_lines() == 1 ->
                print("line, region, average, sale, salesperson")
        @r == 1 ->
                print("$.variables.line, $.headers.region, $.variables.ave, $.headers.sale, $.headers.seller")
    ]
```

3. Validate a file

```bash
    [ ~Apply five rules to check if this file meets expectations~
        @last_age.onchange = @current_age
        @current_age = #age

        length(#lastname)==30           -> print("$.csvpath.line_count: lastname $.headers.lastname is > 30")
        not( column(2) == "firstname" ) -> print("$.csvpath.line_count: 3rd header must be firstname, not $headers.2")
        not(any(header()))              -> print("$.csvpath.line_count: check for missing values")
        not(in(#title, "ceo|minon"))    -> print("$.csvpath.line_count: title cannot be $.headers.title")
        gt(@last_age, @current_age)     -> print("$.csvpath.line_count: check age, it went down!")
    ]
```

4. Find a first value

```bash
    [ ~ Find the first times fruit were the most popular and the most recent popular fruit ~
        @fruit = in( #food, "Apple|Pear|Blueberry")
        exists( @fruit.asbool )
        first.year.onmatch( #year )
        @fruit.asbool -> print("$.headers.food was the most popular food for the first time in $.headers.year")
        last.nocontrib() -> print("First years for a type of fruit: $.variables.year")
    ]
```

5. Keep it simple

This works:

```bash
    $/User/fred/some_dir/csvpaths/test.csv[*][
        line_count() == 1 -> print("$.csvpath.headers")
        not( line_count() == 1 ) -> stop()
    ]
```

This is better:

```bash
    $test[*][
        line_count() == 1 -> print("$.csvpath.headers")
        not( line_count() == 1 ) -> stop()
    ]
```

Still better:

```bash
    $test[*][
        line_count() == 1 -> print("$.csvpath.headers")
        stop()
    ]
```

Moving on up:

```bash
    $test[*][
        firstline() -> print("$.csvpath.headers")
        stop()
    ]
```

Getting there:

```bash
    $test[*][
        print("$.csvpath.headers")
        stop()
    ]
```

Stop here?

```bash
    $test[0][ print("$.csvpath.headers") ]
```

Best:

```bash
    $[0][ print("$.csvpath.headers") ]
```


