
# Jinja

`jinja(inpath, outpath)` renders a <a href='https://palletsprojects.com/p/jinja/'>Jinja</a> template at a path to an output path.

The context includes the same variables as the `print()` function.

| Variable name     | Description                                                           |
|-------------------|-----------------------------------------------------------------------|
|name               | The name of the file. E.g. for `$file.csv[*][no()]` it is `file`.     |
|delimiter          | The file's delimiter                                                  |
|quotechar          | The quote character the file uses to quote columns                    |
|match_count        | The current number of matches                                         |
|line_count         | The current line being processed                                      |
|scan_count         | The current number of lines scanned                                   |
|headers            | The list of header values                                             |
|headers.headername | The value of the named header                                         |
|scan_part          | The scan pattern                                                      |
|match_part         | The match pattern                                                     |
|variables          | The value of variables                                                |
|variables.varname  | The value of the named variable                                       |
|match_json         | A JSON dump of the match part parse tree                              |
|line               | The list of values that is the current line being processed           |
|last_row_time      | Time taken for the last row processed                                 |
|rows_time          | Time taken for all rows processed so far                              |

In your Jinja2 templates use `{{var}}` without the `$.` prefix you use in `print()`.

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



