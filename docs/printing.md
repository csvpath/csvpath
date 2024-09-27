# Printing

Validation is more about communication than you might think. We don't typically just want a yes/no result from a validation run. We want to know exactly what the problems are, why, and where. The more human-friendly a validation tool is the more useful it is. For that reason, the `print()` function, along with its friends, is very important.

- [Jinja and tables](#jinja)
- [References](#references)
- [Escaping](#escaping)
- [Qualifiers](#qualifiers)
- [Printers](#printers)
- [Results and printouts](#results)

<a name="print"></a>
## Print

`print()` is the main way of printing in CsvPaths. It is fast, flexible, and both human and machine friendly, in that results are easily available to both. Most of this page is about `print()`.

<a name="jinja"></a>
## Jinja
CsvPath provides Jinja as a way to create fancier output for special purposes. Using Jinja is slower and very much out of band. `jinja()` has a few limitations:
- It requires CsvPaths because it populates the Jinja context with results from the ResultsManager
- Currently, `jinja()` only provides results values from the first csvpath in a named-results set. It will collect values from multiple named-paths, but just from the first path in each.
- Jinja is also, as currently used, not a great fit with highly dynamic systems because it needs a file system path for its template and its output. If CsvPath is being spun up in an unpredictable way on transitory infrastructure, `jinja()` may be challenging or require integration effort.

These limitations are easily addressed; however, we are awaiting more real-world feedback to see where to take `jinja()`.

The Jinja context includes a small number of options from the <a href='https://pypi.org/project/inflect/'>inflect</a> project. You can use the following methods from that library:
- Use inflect's `plural(word)` as `plural(word)`
- `capitalize()` as `cap(word)`
- `a(word)` as `article(word)`

<a name="tables"></a>
## The tables functions

The tables functions include:
- `header_table()` lists all headers with their indexes
- `row_table()` presents all or a from-to set of header values by header index
- `var_table()` gives prints all, some or one variable
- `run_table()` lays out all the runtime metadata that you would use the reference types `metadata` and `csvpath` to access

These functions use the excellent <a href='https://pypi.org/project/tabulate/'>tabulate</a> project to create handsome tables on the command line or in `Printer` instance printouts. Tables are printed using the same plumbing as `print()`.

<a name="references"></a>
## References

Print references are similar to match component references and the reference structure of a csvpath as a whole. To recap:

- Csvpaths follow the reference form by starting with $ and a data identifier, in this case a file path or named-file name
- Match component references have the form: `$` _data identifier_ `.` _reference data type_ (headers or variables) `.` _data item identifier_
- Print references are the same as match component references except:
    - They allow for `$.` to take the place of the data identifier, meaning the current csvpath the `print()` is embedded in, and
    - They offer four reference data types, not just two

The biggest difference between regular references and print references is the reference data types. Print has four:
- `csvpath` - the dynamic runtime metadata
- `metadata` - the static metadata parsed from comments
- `headers`
- `variables`

Other differences include:
- Print references to stack variables can take a number to indicate the index in the stack or `.length` to get the size of the stack
- Print references give access to individual header values within the currently running csvpath. Match component references allow look-ups into past runs, including the results of specific paths within a named-paths set.

<a name="escaping"></a>
## Escaping

Print requires two minor changes to your strings in certain circumstances:

- Print references require an escape for any period directly following a reference. The escape is to double dot: `..`
- `print()` allows for quoted header, same as match component header; however, in `print()` you must use single-quotes, not double-quotes

<a name="qualifiers"></a>
## Qualifiers

The `print()` function can take three qualifiers:
- `onmatch`
- `once`
- `onchange`

`onmatch` you know from other functions, it matches when all the rest of the match components match. `once` does just what it says, it allows `print()` to happen just one time.

`onchange` also does what it says. It calculates the print output and checks to see if it printed that on the previous line. If it did, it does not print the same again; otherwise, it prints. Bear in mind that a single character, including trailing whitespace, could be the difference between two otherwise seemingly same lines. Also remember that `print()` forgets what it printed before the most recent line. If you had an alternating value, `onchange` would not save you from printing at every line.

<a name="printers"></a>
## Printers

The print functions send their output to printers. In CsvPath the default printer is the `StdOutPrinter` that prints to the command line. StdOut is useful for all sorts of things, including creating new CSV files from the output of a csvpath run. When you use CsvPaths, it additionally assigns `Result` instances to be printers for CsvPath. By default, `Result`s just capture the printouts to a list in memory.

You can add more printers to CsvPath or CsvPaths. At the moment the only other `Printer` type is `LogPrinter`, which prints to the log at the `info` level or the level you choose. The interface for printers is simple. Implementing your own would be straightforward.

<a name="results"></a>
## Results and their printouts

CsvPaths keeps csvpath run results in a set of named `Result` instances, one for each CsvPath that ran a csvpath in the named-paths set. As well as identifying its csvpath and file path, a result object has several things:
- A list of errors, if there were any
- A CsvPath instance, along with its end-state variables and other information
- Any matched data lines, if the run was configured to capture lines
- A list of any printout lines generated by `print()`

Result instances printout lines can be used to create reports, emails, or other output that goes beyond the command line. Additionally, since a `Result` has access to all the end-state of a run, it can be used to generate all kinds of reportage around the `print()` output.


