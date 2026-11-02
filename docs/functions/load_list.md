
# Load List

`load_list()` loads a list of values, one per line, from a text file. Its value is the list, which `in()` and other functions can use:

```bash
    @ids.tmp = load_list("ids")
    in( #id, @ids )
```

This matches lines whose `id` header value is in the list.

## Where the list comes from

In a named-paths group run, the argument is the list's name. The list is a file in the group's assets: `<group home>/assets/<name>.txt`. List names are letters, digits, `.`, `_` and `-`, starting with a letter or digit, without the `.txt`. You store a list with the paths manager's asset manager:

```python
    paths.paths_manager.asset_manager.store_list(
        name="orders", list_name="ids", values=["A100", "A101"]
    )
```

In a group run the list must be the group's. A list that is not in the group's assets is an error, even if a file of that name exists somewhere else.

Outside a named-paths group run, for example with a single `CsvPath`, the argument is the path of a `.txt` file:

```bash
    $orders.csv[*][ in( #id, load_list("lists/ids.txt") ) ]
```

## Values

- One value per line, UTF-8.
- Blank lines are skipped.
- Each value is stripped of surrounding whitespace. Nothing else is changed: no case folding and no splitting on `|`.
- The list is a tuple, so it cannot be changed during the run.

## Loaded once

The list is loaded once, when the csvpath's match components are validated, before any line is read. Every line sees the same list. Changing the file during a run changes nothing.

A list that cannot be loaded is an error at that time, before any line is read. That covers a missing file, a path that is not a `.txt` file, and a group list that isn't in the group's assets. The error is reported, the run is marked invalid and stopped, and the error is raised unless the validation mode says not to raise.

The argument must be a string, because the list is loaded before any line is read.

## Keeping lists out of vars.json

A list assigned to a variable is stored in `vars.json` like any other variable. Use the `tmp` qualifier to keep a large list out:

```bash
    @ids.tmp = load_list("ids")
```

Or use `load_list()` directly in `in()`, with no variable at all:

```bash
    in( #id, load_list("ids") )
```
