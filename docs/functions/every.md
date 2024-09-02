
# Every

Matches every N times a value is seen. Every takes two arguments: a value in the form of a function, header, or variable
and an int that indicates how many of the value must be seen for the counter to be increased.

Every creates two variables. One tracks the number of times a value is seen. The other tracks the number of times every() matched or didn't match.

## Examples

    $file.csv[*]
    [
            @t.onmatch=count()
            every.who(#lastname, 2)
    ]


This path matches every other time the value of the `lastname` is seen before. It results in a variable like:

    {'who_every': {'lastname': 1, 'Kermit': 1, 'Bat': 7}, 'who': {False: 6, True: 3}, 't': 3}

This result indicates that the lastname column had:
- 1 'lastname'
- 1 'Kermit'
- 7 'Bat'

Those counts resulted in 3 matches and 6 times no match. 'lastname' and 'Kermit' didn't match because they only appear 1 time each. We would have to see 'Kermit' 2 times in order to get a match on 'Kermit'.


    $file.csv[*]
    [
            @t.onmatch=count()
            every.fish(#lastname=="Bat", 2)
    ]

For a certain .csv file, this path matches 3 times and returns variables like:

    {'fish_every': {False: 2, True: 7}, 'fish': {False: 5, True: 4}, 't': 4}

This means that `#lastname` was "Bat" seven times. There were 2 times `#lastname` was not "Bat". This result could be problematic because it doesn't indicate which rows it collects are the `False` rows and which were the `True` ones. If we care only about the `True` matches, we could filter out the `False` rows by selecting for `#lastname == "Bat" only.

    $file.csv[*]
    [
            @t.onmatch=count()
            every.fish(#lastname=="Bat", 2)
            #lastname=="Bat"
    ]

This results in `t==3` and the list of matched rows including only the 3 matched rows. The variables look like:

    {'fish_every': {False: 2, True: 7}, 'fish': {False: 5, True: 4}, 't': 3}







