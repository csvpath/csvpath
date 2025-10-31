# Scanning

The scanning part of a csvpath enumerates selected lines. The selected lines are passed to the matching part for evaluation. At each line returned, the line number, the scanned line count, and the match count are available.

The scanning part of a csvpath comes after the root. The root is a dollar sign that may be followed by a file path. The scanning instructions come next, in a bracket.

The form is:
```
    $root[*][]
```
Which is often shortened to:
```
    $[*][]
```
The asterisk is the scanning instruction.

The scanning instruction symbols are:
- `*` - A wildcard that matches all lines to the end of the file. It always comes last.
- `-` - The span between two numbers
- `+` - Scans exactly the line number following the `+`

You can put these symbols together with line numbers (zero-based) in several ways:
- `[*]` means all
- `[3*]` means starting from line 4 and going to the end of the file
- `[3]` by itself means just line 4
- `[1-3]` means lines 1 through 4
- `[1+3]` means lines 1 and line 4
- `[1+3-8]` means line 1 and lines 4 through eight
- `[1+3-8+100]` means line 1 and lines 4 through eight and line 100
- `[1+3-8+100*]` means line 1 and lines 4 through eight and line 100 to the end of the file

The most common scanning instructions are:
- `[*]` - to scan the whole file
- `[1*]` - to skip the header line but then scan every line to the end of the file

In the latter case, the Framework still recognizes the headers in the first line and uses them. It just ignores them as data.

If you knew for sure there would be three blank lines at the top of every CSV sheet you handle, you could use a scanning instruction to skip to the headers, and then process the file as if the blank lines didn't exist. That would look like:

```
    $[3*][
        firstline(reset_headers(skip()))
    ]
```




