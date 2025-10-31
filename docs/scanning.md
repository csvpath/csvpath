# Scanning

The scanning part of a csvpath enumerates selected lines. For each line returned, the line number, the scanned line count, and the match count are available.

The scan part of a csvpath starts with a dollar sign to indicate the file root. After the dollar sign comes the file path. The scanning instructions are next, in a bracket.

The form is:
```
    $root[*][]
```
Which can often be shortened to:
```
    $[*][]
```
The asterisk is the scanning instruction.

The symbols are:
- `*` is a wildcard that matches all lines to the end of the file. It always comes last.
- `-` means the span between two numbers
- `+` tells the Framework to scan exactly that line

You can put these symbols together with line numbers (zero-based) in several ways.

The rules are:
- `[*]` means all
- `[3*]` means starting from line 3 and going to the end of the file
- `[3]` by itself means just line 3
- `[1-3]` means lines 1 through 3
- `[1+3]` means lines 1 and line 3
- `[1+3-8]` means line 1 and lines 3 through eight
- `[1+3-8+100]` means line 1 and lines 3 through eight and line 100
- `[1+3-8+100*]` means line 1 and lines 3 through eight and line 100 to the end of the file

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




