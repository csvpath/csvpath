
# Count

Returns the number of matches. When used alone count() gives the total matches seen up to the current line in the file.

Matches can be scoped down to a contained existance test or equality. Counting an equality means a function, term, variable, or header compared to another function, term, variable, or header.

When the counted match is scoped to the contained existance or equality, the count is of values seen. When counting values seen the count function stores the value-integer pairs in a dict within CsvPath's variables under a key identifying the count function. The ID of the count function is a hash by default, making it difficult for a human to understand which count the key represents. To name the count use a qualifier on the count function. A qualifier is a name that follows the function name separated by a dot, as:

    count.my_named_count(#0=True)

For example you can do do something like this:

    $file.csv [*]
              [
                 @t.onmatch=count.firstname_match(#firstname=="Ants")
                 #firstname=="Ants"
              ]

This path counts the number of matches of firstname into the path's variables so that the variable name is like:

    {'firstname_match':{True:1}}


## Examples



