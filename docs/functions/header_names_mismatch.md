
# Header Names Mismatch

`header_names_mismatch()` inspects the CSV headers in comparison to a delimited list of expected headers. The expected headers are listed in a | separated string. For e.g.:

```bash
    header_names_mismatch("firstname|lastname|say")
```

The match result of `header_names_mismatch()` is the boolean comparison of the number of headers found in the delimited list versus the count of those found in the exact same positions in the file headers line.

`header_names_mismatch()` creates more information than just its yea or nay answer. Behind the scenes the function creates four stack variables:

- Present
- Unmatched
- Duplicated
- Misordered

Each stack includes the header names that fit the description, according to the expected values. By default, the stacks are stored at `header_names_mismatch_present`, `header_names_mismatch_unmatched`, `header_names_mismatch_duplicated`, and `header_names_mismatch_misordered`. Use an arbitrary name qualifier to pick another name.

These stacks are calculated one time. The first row scanned wins. However, if you do `reset_headers()` the name mismatch stacks will be deleted and rebuilt. CsvPath finds the stacks by comparing the key endings. It is unlikely, but not impossible, that you could lose an unrelated variable that just happened to end in `_duplicated` when you reset headers. In that unlikely event, you would see a warning in the logs.

`line()` is also worth considering. You can achieve some of the same results with `line()`. `line()` offers more type checking while producing less analytics on any mismatch.

## Examples

```bash
    $[*][ header_names_mismatch.chk("firstname|lastname|say") ]
```

This path matches every line if the header row matches expectations. It generates this JSON data:

```json
    {
        "chk_present": [
            "firstname",
            "lastname",
            "say"
        ],
        "chk_unmatched": [],
        "chk_misordered": [],
        "chk_duplicated": [],
    }
```




