
## last()
Last

Evaluates True on the last line to be scanned.

last() used by itself will always run, even if its line turns out to
be blank and would otherwise be skipped. When last() is composed
within other functions it loses that ability to run no matter what.
For e.g. last() -> print("will always run") vs. and(yes(), last()) ->
print("runs if the last scanned line is not blank")

Optionally, last() can take a function that will be evaluated when
last() evaluates to True. This function, if provided, will not
necessarily be the last evaluation of the run, but will happen only on
the last line. At this time a last() that has an encapsulated function
will correctly run on the last line but it will not produce True in
assignment. Changing that behavior is on the todo list. It should not
be relied on.

| Data signatures                    |
|:-----------------------------------|
| last( [eval on last: None ǁ Any] ) |

| Call signatures                                        |
|:-------------------------------------------------------|
| last( [eval on last: Function ǁ Variable ǁ Equality] ) |

| Purpose    | Value                            |
|:-----------|:---------------------------------|
| Main focus | last() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


