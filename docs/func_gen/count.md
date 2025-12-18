
## count()

Count

Returns the number of matches.

When used alone count() gives the total matches seen up to the current
line in the file.

Matches can be scoped down to a contained existence test or equality.
Counting an equality means a function, term, variable, or header
compared to another function, term, variable, or header.

When count() is scoped to its contained value, the count is of the
values seen. If it is a bool, the count is the number of Trues and the
number of Falses. If an int, it is a count of each value seen.

For example, take count( empty( #zipcode ) )

This use of count() counts the number of times it sees True and False.
Whereas, count( #zipcode ) Counts the number of times each value of
zipcode is seen.

When counting the values it sees, count() stores the value-integer
pairs in a variable under a key identifying the count function. The ID
of the count function is a hash by default, making it difficult for a
human to understand which count the key represents. To name the count
use a qualifier count().

A name qualifier is a name that follows the function name separated by
a dot. For example: count.red_cars(#0="red").

count() can take the onmatch qualifier. When there is a contained
value and onmatch, count only increments if its contained value
matches. For example: $[*][count.onmatch(
in(#firstname,"Bug|Bird|Ants") ) == 2]

This path counts first names that match the in() function. If the
count equals 2 the row will also match. This is a different behavior
from that of other match components in that count is using onmatch to
look inward, rather than at its siblings. Bear in mind, count()
without a contained value only increments when the row matches. In
that case, onmatch would add nothing.

| Data signatures                  |
|:---------------------------------|
| count()                          |
| count( [eval: None ǁ Any], ... ) |

| Call signatures                 |
|:--------------------------------|
| count()                         |
| count( [eval: Matchable], ... ) |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | count() produces a calculated value |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |


