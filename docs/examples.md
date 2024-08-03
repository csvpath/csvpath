
# Examples

These are simple examples of csvpath match parts. Test them yourself before relying on them. See the unit test for more simple path ideas.

1. Find a value
<pre>
    [ ~A running average of ages between 5 and 85~
        gt(#age, 4)
        lt(#age, 86)
        @average_age.onmatch = average(#age, "match")
        last() -> print("The average age between 5 and 85 is $.variables.average_age")
    ]
</pre>

2. Create a file
<pre>
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
</pre>

3. Validate a file
<pre>
    [ ~Apply five rules to check if this file meets expectations~
        @last_age.onchange = @current_age
        @current_age = #age

        length(#lastname)==30           -> print("$.line_count: lastname $.headers.lastname is > 30")
        not( column(2) == "firstname" ) -> print("$.name: 3rd header must be firstname, not $headers.2")
        not(any(header()))              -> print("$.line_count: check for missing values")
        not(in(#title, "ceo|minon"))    -> print( "$.line_count: title cannot be $.headers.title")
        gt(@last_age, @current_age)     -> print( "$.line_count: check age, it went down!")
    ]
</pre>







