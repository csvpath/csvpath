
# CsvPath

CsvPath defines a declarative syntax for inspecting and updating CSV files. Though much simpler, it is similar to:
- XPath: CsvPath is to a CSV file like XPath is to an XML file
- Schematron: Schematron validation is basically XPath rules applied using XSLT. CsvPath paths can be used as validation rules.
- CSS selectors: CsvPath picks out structured data in a conceptually similar way to how CSS selectors pick out HTML structures.

CsvPath is intended to fit with other DataOps and data quality tools. Files are streamed. The interface is simple. Custom functions can be added.

# Usage
CsvPath paths have three parts:
- a "root" file name
- a scanning part
- a matching part

The root starts with `$`. The match and scan parts are enclosed by brackets.

A very simple csvpath might look like this:

    $filename[*][yes()]

This path says open the file named `filename`, scan all the lines, and match every line scanned.

The filename following the `$` can be an actual relative or absolute file path. It could alternatively be a logical identifier that points indirectly to a physical file, as described below.

This is a very basic use. For more usage, see the unit tests.

    path = CsvPath(delimiter=",")
    path.parse("""$test.csv
                    [5-25]
                    [#0=="Frog" @lastname="Bats" count()==2]""")
    for i, line in enumerate( path.next() ):
        print(f"{i}: {line}")
    print(f"path vars: {path.variables}")

The csvpath says:
- Open test.csv
- Scan lines 5 through 25
- Match the second time we see a line where the first column equals "Frog" and set the variable called  "lastname" to "Bats"

You can use the `CsvPaths` class to set up a list of named file paths so that you can have more concise csvpaths. Named paths can take the form of:
- A JSON file with a dictionary of file paths under name keys
- A dict object passed into the CsvPaths object containing the same named path structure
- The path to a csv file that will be put into the named paths dict under its name minus extension
- A file system path pointing to a directory that will be used to populate the named paths dict with all contined files

You can then use a csvpath like `$logical_name[*][yes()]` to apply the csvpath to the file named `logical_name` in the CsvPaths object's named paths dict. This use is nearly transparent:

    paths = CsvPaths(filename = "my_named_paths.json")
    path = paths.csvpath()
    path.parse( """$test[*][#firstname=="Fred"]""" )
    path.collect()

If my_named_paths.json contains the following structure, the name `test` will be used to find `tests/test_resources/test.csv`. The parse method will apply the csvpath and the collect method will gather all the matched rows.

    { "test":"test/test_resources/test.csv" }

# Scanning
The scanner enumerates lines. For each line returned, the line number, the scanned line count, and the match count are available. The set of line numbers scanned is also available.

The scan part of the path starts with a dollar sign to indicate the root, meaning the file from the top. After the dollar sign comes the file path. The scanning instructions are in a bracket. The rules are:
- `[*]` means all
- `[3*]` means starting from line 3 and going to the end of the file
- `[3]` by itself means just line 3
- `[1-3]` means lines 1 through 3
- `[1+3]` means lines 1 and line 3
- `[1+3-8]` means line 1 and lines 3 through eight

# Matching
The match part is also bracketed. Matches have space separated components or "values" that are ANDed together. The components' order is important. A match component is one of several types:
<table>
<tr>
<td>Type</td>
<td>Returns</td>
<td>Matches</td>
<td>Description</td>
<td>Examples</td>
</tr>
    <tr>
        <td>Term </td><td> Value </td><td> True when used alone, otherwise calculated </td>
        <td>A quoted string or date, optionally quoted number, or
        regex. Regex features are limited. A regex is wrapped  in "/" characters and
only has regex functionality when used in the regex() function.</td>
        <td>
            <li/> `"Massachusetts"`
            <li/> `89.7`
            <li/> `/[0-9a-zA-Z]+!/`
        </td>
    </tr>
    <tr>
        <td>Function </td><td> Calculated   </td><td> Calculated </td>
        <td>A function name followed by parentheses. Functions can
contain terms, variables, headers and other  functions. Some functions
take a specific or  unlimited number of types as arguments.
Certain functions can take qualifiers. An `onmatch` qualifier indicates that
the function should be applied only when the whole path matches.
Some functions optionally take an arbitrary name qualifier to better name a tracking variable.
Qualifiers are described below.  </td>
        <td>
            <li/> `not(count()==2)`
            <li/> `add( 5, 3, 1 )`
            <li/> `concat( end(), regex(#0, /[0-5]+abc/))`
        </td>
    </tr>
    <tr>
        <td>Variable </td>
        <td>Value</td>
        <td>True/False when value tested. True when set, True/False existence when used alone</td>
        <td>An @ followed by a name. A variable is
            set or tested depending on the usage. By itself, it is an existence test. When used as
            the left hand side of an "=" its value is set.
            When it is used on either side of an "==" it is an equality test.
            Variables can take an `onmatch` qualifier to indicate that the variable should
only be set when the row matches all parts of the path.
        <td>
            <li/> `@weather="cloudy"`
            <li/> `count(@weather=="sunny")`
            <li/> `@weather`
            <li/> `#summer==@weather`

#1 is an assignment that sets the variable and returns True. #2 is an argument used as a test in a way that is specific to the function. #3 is an existence test. #4 is a test.
        </td>
    </tr>
    <tr>
        <td>Header   </td>
        <td>Value     </td>
        <td>A True/False existence test when used alone, otherwise calculated</td>
        <td>A # followed by a name or integer. The name references a value in line 0, the header
 row. A number references a column by the 0-based column order.   </td>
        <td>
            <li/> `#firstname`
            <li/> `#3`
        </td>
    </tr>
    <tr>
        <td>Equality</td>
        <td>Calculated   </td>
        <td>True at assignment, otherwise calculated   </td>
        <td>Two of the other types joined with an "=" or "==".</td>
        <td>
            <li/> `@type_of_tree="Oak"`
            <li/> `#name == @type_of_tree`
        </td>
    </tr>
<table>

A variable can be assigned early in the match part of a path and used later in that same path. The assignment and use will both be in the context of the same row in the file. For e.g.

    [@a=#b #c==@a]

Can also be written as:

    [#c==#b]

Variables and some functions can take qualifiers on their name. A qualifier takes the form of a dot plus a qualification name. At the moment there are only two qualifiers:

- `onmatch` to indicate that action on the variable or function only happens when the whole path matches a row
- An arbitrary string to add a name for the function's internal use, typically to name a variable

Qualifiers look like:

    [ @myvar.onmatch = yes() ]

Or:

    [ @i = increment.this_is_my_increment.onmatch(yes(), 3) ]

When multiple qualifiers are used order is not important.

## Example
    [ #common_name #0=="field" @tail.onmatch=end() not(in(@tail, 'short</td><td>medium')) ]

In the path above, the rules applied are:
- `#common_name` indicates a header named "common_name". Headers are the values in the 0th line. This component of the match is an existence test.
- `#2` means the 3rd column, counting from 0
- Functions and column references are ANDed together
- `@tail` creates a variable named "tail" and sets it to the value of the last column if all else matches
- Functions can contain functions, equality tests, and/or literals

Variables are always set unless they are flagged with `.onmatch`. That means:

    $file.csv[*][ @imcounting.onmatch = count_lines() no()]

will never set `imcounting`, but:

    $file.csv[*][ @imcounting = count_lines() no()]

will always set it.

Most of the work of matching is done in functions. The match functions are the following.


<table>
<tr><th> Group     </th><th>Function                       </th><th> What it does                                              </th></tr>
<tr><td> Boolean   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/any.md'>any(value, value)</a>  </td><td> existence test across a range of places </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/no.md'>no()</a>  </td><td> always false                                  </td></tr>
<tr><td>           </td><td> not(value)                    </td><td> negates a value                                           </td></tr>
<tr><td>           </td><td> or(value, value,...)          </td><td> match any one                                             </td></tr>
<tr><td>           </td><td> yes()                         </td><td> always true                                               </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/in.md'>in(value, list)</a>  </td><td> match in a pipe-delimited list    </td></tr>
<tr><td> Math      </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> add(value, value, ...)        </td><td> adds numbers                                              </td></tr>
<tr><td>           </td><td> divide(value, value, ...)     </td><td> divides numbers                                           </td></tr>
<tr><td>           </td><td> multiply(value, value, ...)   </td><td> multiplies numbers                                        </td></tr>
<tr><td>           </td><td> subtract(value, value, ...)   </td><td> subtracts numbers                                         </td></tr>
<tr><td>           </td><td> after(value)                  </td><td> finds things after a date, number, string                 </td></tr>
<tr><td>           </td><td> before(value)                 </td><td> finds things before a date, number, string                </td></tr>
<tr><td> Stats     </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/average.md'>average(number, type)</a> </td><td> returns the average up to current "line", "scan", "match" </td></tr>
<tr><td>           </td><td> median(value, type)           </td><td> median value up to current "line", "scan", "match"        </td></tr>
<tr><td>           </td><td> max(value, type)              </td><td> largest value seen up to current "line", "scan", "match"  </td></tr>
<tr><td>           </td><td> min(value, type)              </td><td> smallest value seen up to current "line", "scan", "match" </td></tr>
<tr><td>           </td><td> percent(type)                 </td><td> % of total lines for "scan", "match", "line"              </td></tr>
<tr><td> Counting  </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/count.md'>count()</a> </td><td> counts the number of matches            </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/count.md'>count(value)</a> </td><td> count matches of value              </td></tr>
<tr><td>           </td><td> count_lines()                 </td><td> count lines to this point in the file                     </td></tr>
<tr><td>           </td><td> count_scans()                 </td><td> count lines we checked for match                          </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/first.md'>first(value, value, ...)</a> </td><td> match the first occurrence and capture line  </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/increment.md'>increment(value, n)</a> </td><td> increments a variable by n each time seen   </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/every.md'>every(value, number)</a> </td><td> match every Nth time a value is seen  </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/tally.md'>tally(value, value, ...)</a></td><td> counts times values are seen, including as a set   </td></tr>
<tr><td> Strings   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> concat(value, value)          </td><td> joins two values                 </td></tr>
<tr><td>           </td><td> length(value)                 </td><td> returns the length of the value                           </td></tr>
<tr><td>           </td><td> lower(value)                  </td><td> makes value lowercase                                     </td></tr>
<tr><td>           </td><td> regex(regex-string, value)    </td><td> match on a regular expression                             </td></tr>
<tr><td>           </td><td> substring(value, int)         </td><td> returns the first n chars from the value                  </td></tr>
<tr><td>           </td><td> upper(value)                  </td><td> makes value uppercase                                     </td></tr>
<tr><td> Columns   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> end()                         </td><td> returns the value of the last column                      </td></tr>
<tr><td>           </td><td> column(value)                 </td><td> returns column name for an index or index for a name      </td></tr>
<tr><td> Other     </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> header()                      </td><td> indicates to another function to look in headers       </td></tr>
<tr><td>           </td><td> isinstance(value, typestr)    </td><td> tests for "int","float","complex","bool","usd"            </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/now.md'>now(format)</a></td><td> a datetime, optionally formatted       </td></tr>
<tr><td>           </td><td> <a href='csvpath/matching/functions/print.md'>print(value, str)</a></td><td> when matches prints the interpolated string  </td></tr>
<tr><td>           </td><td> random(starting, ending)      </td><td> generates a random int from starting to ending            </td>
<tr><td>           </td><td> <a href='csvpath/matching/functions/stop.md'>stop(value)</a> </td><td> stops path scanning if a condition is met                 </td>
<tr><td>           </td><td> <a href='csvpath/matching/functions/when.md'>when(value, value)</a> </td><td> activate a value when a condition matches   </td>
<tr><td>           </td><td> variable()                    </td><td> indicates to another function to look in variables       </td></tr>
</tr>
</table>

# Not Ready For Production
Anything could change and performance could be better. This project is a hobby.













