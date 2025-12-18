
## stop()

Halts the run abruptly.

When stop() contains no other match components it simply stops the
run.

When stop contains another match component, stop() is conditional to
its evaluation. In this way stop() functions like a when/do
expression. This functionality convenient in some cases and adds
additional composability.

stop() will not necessarily prevent other match components in its
csvpath from being evaluated. Match components that come earlier in
the csvpath will be evaluated as normal. Match components that have
the onmatch qualifier are evaluated at the end of the csvpath, and so
might not be evaluated when stop() happens even if they come before
stop().

| Data signatures                 |
|:--------------------------------|
| stop( [eval this: None ǁ Any] ) |

| Call signatures                          |
|:-----------------------------------------|
| stop( [eval this: Function ǁ Equality] ) |

| Purpose    | Value                   |
|:-----------|:------------------------|
| Main focus | stop() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


