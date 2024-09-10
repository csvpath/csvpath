
# Jinja

`jinja(inpath, outpath)` renders a <a href='https://palletsprojects.com/p/jinja/'>Jinja</a> template at a path to an output path.

This function takes the follow args:
- The path to the template
- The path to where the result should be saved
- Any number of named-result names that should be accessible within the template

The context includes the same reference data as you use in the `print()` function:
- variables
- headers
- metadata
- csvpath _(the runtime data)_

As with `print()`, at this time, you only have access to the most recent line in the file. This limitation will very likely be removed in the future.

You access the variables in a similar way; however, the reference format changes from:

```bash
    $.variables.my_var.its_tracking_val
```

To the very similar:

```bash
    {{ local.variables.my_var.its_tracking_val
```

Basically, just drop the root `$` and add a `local` to reference the current csvpath.

If you want to reference any other csvpath results, just replace `local` with the name of that path. Keep in mind that at this time you can only reference the most recent result of a named-result group. This limitation will very likely be removed in the future.

## The `csvpath` variables

| Variable name     | Description                                                           |
|-------------------|-----------------------------------------------------------------------|
|name               | The name of the file. E.g. for `$file.csv[*][no()]` it is `file`.     |
|delimiter          | The file's delimiter                                                  |
|quotechar          | The quote character the file uses to quote columns                    |
|count_matches      | The current number of matches                                         |
|count_lines        | The current line being processed                                      |
|count_scans        | The current number of lines scanned                                   |
|headers            | The list of header values                                             |
|scan_part          | The scan pattern                                                      |
|match_part         | The match pattern                                                     |
|match_json         | A JSON dump of the match part parse tree                              |
|line               | The list of values that is the current line being processed           |
|last_row_time      | Time taken for the last row processed                                 |
|rows_time          | Time taken for all rows processed so far                              |

The context also contains three functions that expose linguistic support from the <a href='https://pypi.org/project/inflect/'>Inflect library</a>.

    def _plural(self, word):
        return self._engine.plural(word)

    def _cap(self, word):
        return word.capitalize()

    def _article(self, word):
        return self._engine.a(word)

These are added to the context as:

    tokens["plural"] = self._plural
    tokens["cap"] = self._cap
    tokens["article"] = self._article


For e.g., use `{{plural("elephant")}}` to get the plural `elephants` in your output file.

Be aware that using `jinja()` may impose a high startup cost that you pay at template render time. 1 to 2 seconds latency would not be surprising.

## Examples

This csvpath renders template `csv_file_stats.html` to a location in the `renders` directory.

    $file.csv[*][
        last.nocontrib() -> jinja("templates/csv_file_stats.html", concat("renders/", count(), ".html") )
    ]



