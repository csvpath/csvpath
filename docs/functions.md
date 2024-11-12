
# Functions

Most of the work of matching is done in match component functions. There are over one hundred functions in several groups.

- [Boolean](#boolean)
- [Counting](#counting)
- [Dates](#dates)
- [Headers](#headers)
- [Lines](#lines)
- [Math](#math)
- [Misc](#misc)
- [Print](#print)
- [Stats](#stats)
- [Strings](#strings)
- [Testing](#testing)
- [Types](#types)
- [Validity](#validity)
- [Variables](#variables)

## Overview

Functions perform work within a csvpath. Some focus on creating values. Others on deciding if a line matches. And a few provide a side-effect, rather than contributing values or matching.

Like a Python function, a CsvPath function is represented by a name followed by parentheses. They may take zero to an unlimited number of arguments within the parentheses, separated by commas.

Functions can contain:
- Terms
- Variables
- Headers
- Equality tests
- Variable assignment
- Other functions

They can not include when/do expressions. This means you cannot use `->` within a function.

Many functions take qualifiers. With only a three exceptions, all functions can take the `onmatch` qualifier. An `onmatch` qualifier indicates that the function should be applied only when the whole path matches. See the individual function pages for what built-in qualifiers a function supports.

Some functions will optionally make use of an arbitrary name qualifier to better name a tracking variable.

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/qualifiers.md'>Read about qualifiers here.</a>

## Custom Functions

Creating your own function is easy. Once you create a function, you register it with the `FunctionFactory` class. You can register your functions either programmatically or by creating an import file listing your functions. Your import file must be referenced in your `config.ini` file at `[functions][imports]` like this:

    [functions]
    imports = my_project_assets/my_functions.imports

Each custom function has its own line in your imports file. The format is the same as you use for importing classes into Python files -- under the hood the mechanism is similar. E.g.

```python
    from my_function.for_stuff.me import Me as function_me
```

In this example your class is `Me` and the name of the function you use in your csvpath is `function_me()`

Use your functions in csvpaths by simply referring to them by name like you would any built-in function.

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/implementing_functions.md'>Read more about implementing your own functions here.</a>

## A Few Examples

- `not(count()==2)`
- `add( 5, 3, 1 )`
- `concat( end(), regex(/[0-5]+abc/, #0))`

There are lots more simple examples on the individual function pages.

## All the functions



## Boolean
<table>
<tr><th>Function <a name="boolean">  </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/above.md'>after(value, value)</a> </td><td> Finds things after a date, number, string. Aliases: gt(), above().    </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/all.md'>all(value, value, ...)</a>  </td><td> An existence test for all selected values or all headers, or all variables. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/andor.md'>and(value, value,...)</a> </td><td> Returns true when all match.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/any.md'>any(value, value, ...)</a>  </td><td> An existence test across a range of places. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/above.md'>before(value, value)</a></td><td> Finds things before a date, number, string.  Aliases: lt(), below().     </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/between.md'>between(value, value, value)</a> </td><td> Returns true when a value is found between to others. Aliases: outside().     </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/empty.md'>empty(value)</a>    </td><td> Tests if the value is empty. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/empty.md'>exists(value)</a> </td><td> Tests if the value exists.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/in.md'>in(value, list)</a>  </td><td> Match against a pipe-delimited list, values, or references. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/all.md'>missing(value, value, ...)</a>  </td><td> An existence test for all selected values, all headers, or all variables. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/no.md'>no()</a>  </td><td> Always false. Alias: false() </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/not.md'>not(value)</a>  </td><td> Negates a value.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/andor.md'>or(value, value,...)</a>  </td><td> Returns true when any match. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/no.md'>yes()</a> </td><td> Always returns true. Alias: true()   </td></tr>
</table>


## Counting
<table>
<tr><th>Function            <a name="counting"> </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/count.md'>count()</a> </td><td> Counts the number of matches. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/count.md'>count(value)</a> </td><td> Count the matches of values.  </td></tr>
<tr><td> count_lines()      </td><td> count the lines of data to this point in the file. </td></tr>
<tr><td> count_scans()      </td><td> count lines we checked for match   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/counter.md'>counter()</a>  </td><td> a streamlined way to increment a counter variable   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/has_dups.md'>count_dups(header, ...)</a>   </td><td> Returns the number of duplicate lines.   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/every.md'>every(value, number)</a> </td><td> Matches every Nth time a value is seen.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/has_matches.md'>has_matches(header, ...)</a>   </td><td> Matches when any other match component matched anywhere in the file.   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/increment.md'>increment(value, n)</a> </td><td> Increments a variable by n each time seen.   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/line_number.md'>line_number()</a>  </td><td> Gives the physical line number.    </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/tally.md'>tally(value, value, ...)</a></td><td> Counts times values are seen, including as a set.   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/total_lines.md'>total_lines()</a></td><td> Returns the number of rows in the file being scanned.   </td></tr>
</table>

## Dates
<table>
<tr><th>Function            <a name="dates"> </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/now.md'>now(format)</a></td><td> Returns a datetime, optionally formatted, for the current moment.       </td></tr>
</table>



## Headers
<table>
<tr><th>Function   <a name="headers"> </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/replace.md'>append(value, value)</a> </td><td> Appends a new header value at the end of every line.   </td>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/collect.md'>collect(value, ...)</a></td><td> Identifies the header values to collect when a row matches. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/count_headers.md'>count_headers()</a> </td><td> Returns the number of headers expected.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/count_headers.md'>count_headers_in_line()</a> </td><td> Returns the number found in the line.      </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/empty_stack.md'>empty_stack(value, ...)</a>  </td><td> Returns a stack of the names of empty header values. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/end.md'>end(int)</a>  </td><td> Returns the value of the line's last header value. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/header_name.md'>header_name(value, value)</a> </td><td> Returns the header name for an index.      </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/header_name.md'>header_index(value, value)</a> </td><td> Returns the header index for a name.      </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/variables_and_headers.md'>headers(value)</a>  </td><td> Indicates to another function that it should look in the headers.      </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/header_names_mismatch.md'>header_names_mismatch(value)</a>  </td><td> Checks the header names against a delimited list of expected headers.   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/mismatch.md'>mismatch()</a>  </td><td> Returns the difference in number of value vs. number of headers.      </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/replace.md'>replace(value, value)</a> </td><td> Replaces a header value with another value.   </td>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/reset_headers.md'>reset_headers()</a>  </td><td> Sets the headers to the values of the current line.      </td></tr>
</table>

## Lines
<table>
<tr><th>Function            <a name="lines"> </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/advance.md'>advance(int)</a></td><td> Skips the next n-rows </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/after_blank.md'>after_blank()</a></td><td> Matches when a line was preceded by a blank line </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/has_dups.md'>has_dups(header, ...)</a> </td><td> Returns true if there are duplicate lines.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/has_dups.md'>count_dups(header, ...)</a> </td><td> Counts duplicate lines.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/has_dups.md'>dup_lines(header, ...)</a> </td><td> Returns the line numbers of duplicate lines.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/last.md'>firstline()</a></td><td> Matches on the 0th line, if scanned. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/last.md'>firstscan()</a></td><td> Matches on the 1st line scanned. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/last.md'>firstmatch()</a></td><td> Matches on the 1st line matched. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/last.md'>last()</a></td><td> Returns true on the last row that will be scanned. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/first.md'>first(value, value, ...)</a> </td><td> Matches the first occurrence and captures the line number.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/stop.md'>skip(value)</a> </td><td> Skips to the next line scanned if a condition is met.   </td>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/stop.md'>stop(value)</a> </td><td> Stops scanning lines if a condition is met. </td>

</table>



## Math
<table>
<tr><th>Function    <a name="math"></a>     </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>add(value, value, ...)</a>       </td><td> Adds numbers.    </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>divide(value, value, ...)</a>    </td><td> Divides numbers.    </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>mod(value, value)</a>            </td><td> Returns the modulus of two numbers. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>multiply(value, value, ...)</a>  </td><td> Multiplies numbers.   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>round(value)</a>                 </td><td> Rounds a number. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtotal.md'>subtotal(value)</a>              </td><td> Returns a running subtotal of a value subtotaled by another value. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>subtract(value, value, ...)</a>  </td><td> Subtracts numbers or makes a number negative. Aliases: minus(). </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/sum.md'>sum(value)</a>                        </td><td> Returns a running sum of the value. </td></tr>
</table>


## Misc
<table>
<tr><th>Function   <a name="misc">  </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/fingerprint.md'>line_fingerprint()</a>, store_fingerprint(), file_fingerprint()</td><td> Functions for creating digests. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/import.md'>import()</a></td><td> Injects another csvpath into the current csvpath. </td></tr>
<tr><td><a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/random.md'>random(starting, ending)</a></td><td> Generates a random int from starting to ending.</td>
<tr><td><a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/random.md'>shuffle(starting, ending)</a></td><td> Generates a random int from starting to ending with no replacement.</td>
</table>


## Print
<table>
<tr><th>Function            <a name="print"> </th><th> What it does                                              </th></tr>
<tr><td> header_table(value, value) </td><td> Prints a formatted table of the headers with header numbers.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/jinja.md'>jinja(value, value)</a>  </td><td> Applies a Jinja2 template.   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/print.md'>print(str, value)</a></td><td> Prints the interpolated string.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/print_line.md'>print_line(value,value)</a></td><td> Prints the current line unchanged.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/print_line.md'>print_queue(value,value)</a></td><td> Returns the number of strings printed.  </td></tr>
<tr><td> row_table(value, value) </td><td> Prints a formatted table of a row.  </td></tr>
<tr><td> var_table(value, value) </td><td> Prints a formatted table of the variables.  </td></tr>
</table>




## Stats
<table>
<tr><th>Function  <a name="stats">   </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/average.md'>average(number, type)</a> </td><td> Returns the average up to current "line", "scan", "match". </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/correlate.md'>correlate(value, value)</a> </td><td> Gives the running correlation between two values. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/max.md'>max(value, type)</a> </td><td> Returns the largest value seen up to current "line", "scan", "match".  </td></tr>
<tr><td> median(value, type)           </td><td> Returns the median value up to current "line", "scan", "match".  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/max.md'>min(value, type)</a></td><td> Returns the smallest value seen up to current "line", "scan", "match". </td></tr>
<tr><td> percent(type)                 </td><td> Returns the percent of total lines for "scan", "match", "line".   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/percent_unique.md'>percent_unique(header)</a> </td><td> Returns the percent of unique values found in the header values.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/stdev.md'>stdev(stack)</a> and <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/stdev.md'>pstdev(stack)</a> </td><td> Returns the standard deviation of numbers pushed on a stack.  </td></tr>
</table>



## Strings
<table>
<tr><th>Function   <a name="strings">  </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>concat(value, value, ...)</a> </td><td> Joins any number of values.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/regex.md'>exact(regex-string, value)</a> </td><td> Exact match on a regular expression. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>length(value)</a>             </td><td> Returns the length of the value.   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>lower(value)</a>              </td><td> Makes a value lowercase. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>max_length(value)</a>  </td><td> Returns the length of the value.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/metaphone.md'>metaphone(value, value)</a>  </td><td> Returns the metaphone transformation of a string or does a reference look up. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>min_length(value)</a>  </td><td> Returns the length of the value.</td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/regex.md'>regex(regex-string, value)</a> </td><td> Matches on a regular expression. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>starts_with(value, value)</a>   </td><td> Checks if the first value starts with the second. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>strip(value)</a>              </td><td> Trims off whitespace.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>substring(value, int)</a>     </td><td> Returns the first n chars from the value. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>upper(value)</a>              </td><td> Makes a value uppercase.   </td></tr>
</table>


## Testing
<table>
<tr><th>Function            <a name="testing"> </th><th> What it does                                              </th></tr>
<tr><td> brief_stack_trace()    </td><td> Logs a slimmed-down stack trace.    </td></tr>
<tr><td> debug()                </td><td> Changes the log level.       </td></tr>
<tr><td> do_when_stack()        </td><td> Returns a stack with True or False for each do/when to show which activated their right-hand side. </td></tr>
<tr><td> vote_stack()           </td><td> Returns a stack with True or False for each match component's match decision. </td></tr>
</table>


## Types
<table>
<tr><th>Function            <a name="types"> </th><th> What it does                                              </th></tr>
<tr><td>boolean(value)</td><td> A boolean value  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/date.md'>date(value, format)</a></td><td> Returns a date parsed according to a format string.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/date.md'>datetime(value, format)</a></td><td> Returns a datetime parsed according to a format string.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/intf.md'>float(value)</a>    </td><td> A number as a float. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/intf.md'>int(value)</a>    </td><td> A number as an int. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/no.md'>none()</a>                    </td><td> Returns None. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/intf.md'>num(value, int, int, int, int)</a>    </td><td> A number defined as min/max before and after the decimal. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>string(value, max, min)</a> </td><td> Declares a string, optionally with max and min lengths.  </td></tr>
</table>



## Validity
<table>
<tr><th>Function            <a name="validity"> </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/fail.md'>fail()</a>  </td><td> Indicate that the CSV is invalid.   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/fail.md'>failed()</a></td><td> Check if the CSV is invalid.   </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/fail.md'>fail_and_stop()</a></td><td> Stop the scan and declare the file invalid at the same time.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/line.md'>line(function, function, ...)</a></td><td> Declares a typed ordered structure for lines using core data type functions like string(), int(), etc.  </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/fail.md'>valid()</a></td><td> Check if the CSV is valid or invalid.  </td></tr>
</table>

## Variables
<table>
<tr><th>Function            <a name="variables"> </th><th> What it does                                              </th></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/get.md'>get(value, value)</a></td><td> Gets a variable value. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/pop.md'>peek(name, int)</a> </td><td> Accesses a value at an index in a stack.    </td>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/pop.md'>peek_size(name)</a> </td><td> Returns the size of a stack.    </td>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/pop.md'>pop(name)</a> </td><td> Pops a value off a stack.    </td>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/pop.md'>push(name, value)</a> </td><td> Pushes a value on a stack.    </td>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/get.md'>put(value, value)</a></td><td> Sets a variable value. </td></tr>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/pop.md'>stack(name)</a> </td><td> Returns a stack variable of pushed values.   </td>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/track.md'>track(value, value)</a> </td><td> Tracks a value by name.  </td>
<tr><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/variables_and_headers.md'>variables()</a>    </td><td> Indicates to another function that it should look in the variables.  </td></tr>
</table>





