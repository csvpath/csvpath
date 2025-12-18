
Stop
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

| Data signatures               |
|:------------------------------|
| stop( [eval this: [36m[3mNone[0m|[36m[3mAny[0m] ) |

| Call signatures                        |
|:---------------------------------------|
| stop( [eval this: [36m[3mFunction[0m|[36m[3mEquality[0m] ) |

| Purpose    | Value                   |
|:-----------|:------------------------|
| Main focus | stop() is a side-effect |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | [36m[3monmatch[0m     |
| Value qualifiers | [36m[3monmatch[0m     |


