
# Functions

Most of the work of matching is done in match component functions. There are dozens of functions in several groups.

- [Boolean](#boolean)
- [Counting](#counting)
- [Headers](#headers)
- [Math](#math)
- [Misc](#misc)
- [Strings](#strings)
- [Stats](#stats)

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

Certain functions have qualifiers. An `onmatch` qualifier indicates that
the function should be applied only when the whole path matches.

Some functions optionally will make use of an arbitrary name qualifier to better name a tracking variable.
<a href='https://github.com/dk107dk/csvpath/blob/main/docs/qualifiers.md'>Read about qualifiers here.</a>

## Custom Functions

Creating your own function is easy. Once you create a function, you register it with the `FunctionFactory` class. You must register your functions each time you run CsvPath. Use your function in csvpaths by simply referring to it by name like any other function.

<a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/implementing_functions.md'>Read more about implementing your own functions here.</a>

## A Few Examples

- `not(count()==2)`
- `add( 5, 3, 1 )`
- `concat( end(), regex(#0, /[0-5]+abc/))`

There are lots more simple examples on the individual function pages.

## All the functions

<table>
<tr><th> Group     </th><th>Function                       </th><th> What it does                                              </th></tr>
<tr><td>
    <a name="boolean">
    Boolean   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/above.md'>after(value, value)</a> or <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/above.md'>gt(value, value)</a> or <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/above.md'>above( value, value)</a> </td><td> finds things after a date, number, string        </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/above.md'>before(value, value)</a> or <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/above.md'>lt(value, value)</a> or <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/above.md'>below( value, value)</a></td><td> finds things before a date, number, string       </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/between.md'>between(value, value, value)</a> or <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/between.md'>outside(value, value, value)</a> </td><td> returns true when a value is found between to others     </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/all.md'>all(value, value, ...)</a>  </td><td> existence test for all selected values or all headers, or all variables </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/all.md'>missing(value, value, ...)</a>  </td><td> existence test for all selected values, all headers, or all variables </td></tr>



<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/any.md'>any(value, value, ...)</a>  </td><td> existence test across a range of places </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/no.md'>no()</a>  </td><td> always false                                  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/not.md'>not(value)</a>                    </td><td> negates a value                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/andor.md'>and(value, value,...)</a>          </td><td> match all                                             </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/andor.md'>or(value, value,...)</a>          </td><td> match any one                                             </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/no.md'>yes()</a> </td><td> always true                                               </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/empty.md'>empty(value)</a>    </td><td> tests if the value is empty            </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/empty.md'>exists(value)</a> </td><td> tests if the value exists            </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/fail.md'>fail()</a>  </td><td> indicate that the CSV is invalid   </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/fail.md'>failed()</a></td><td> check if the CSV is invalid   </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/fail.md'>fail_and_stop()</a></td><td> stop the scan and declare the file invalid at the same time  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/fail.md'>valid()</a></td><td> check if the CSV is valid or invalid  </td></tr>


<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/in.md'>in(value, list)</a>  </td><td> match in a pipe-delimited list    </td></tr>
<tr><td>
    <a name="math"></a>
    Math      </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td>  <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>add(value, value, ...)</a>        </td><td> adds numbers                                              </td></tr>
<tr><td>           </td><td>  <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>divide(value, value, ...)</a>     </td><td> divides numbers                                           </td></tr>
<tr><td>           </td><td>  <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>multiply(value, value, ...)</a>   </td><td> multiplies numbers                                        </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>subtract(value, value, ...)</a>    </td><td> subtracts numbers or makes a number negative                                        </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>mod(value, value)</a>    </td><td> returns the modulus of two numbers </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>int(value)</a>    </td><td> returns a number as an int </td></tr>


<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/sum.md'>sum(value)</a> </td><td> returns a running subtotal of the value </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/subtract.md'>round(value)</a> </td><td> rounds a number </td></tr>
<tr><td> <a name="stats">
    Stats     </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/average.md'>average(number, type)</a> </td><td> returns the average up to current "line", "scan", "match" </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/correlate.md'>correlate(value, value)</a> </td><td> gives the running correlation between two values </td></tr>
<tr><td>           </td><td> median(value, type)           </td><td> median value up to current "line", "scan", "match"        </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/max.md'>max(value, type)</a> </td><td> largest value seen up to current "line", "scan", "match"  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/max.md'>min(value, type)</a></td><td> smallest value seen up to current "line", "scan", "match" </td></tr>
<tr><td>           </td><td> percent(type)                 </td><td> % of total lines for "scan", "match", "line"              </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/percent_unique.md'>percent_unique(header)</a> </td><td> % of unique values found in the header values  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/stdev.md'>stdev(stack)</a> and <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/stdev.md'>pstdev(stack)</a> </td><td> returns the standard deviation of numbers pushed on a stack  </td></tr>

<tr><td> <a name="counting">
    Counting  </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/count.md'>count()</a> </td><td> counts the number of matches            </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/count.md'>count(value)</a> </td><td> count matches of value              </td></tr>
<tr><td>           </td><td> count_lines()                 </td><td> count the lines of data to this point in the file                     </td></tr>
<tr><td>           </td><td> count_scans()                 </td><td> count lines we checked for match   </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/has_dups.md'>count_dups(header, ...)</a>   </td><td> returns the number of duplicate lines   </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/line_number.md'>line_number()</a>  </td><td> give the physical line number    </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/first.md'>first(value, value, ...)</a> </td><td> match the first occurrence and capture line  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/increment.md'>increment(value, n)</a> </td><td> increments a variable by n each time seen   </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/every.md'>every(value, number)</a> </td><td> match every Nth time a value is seen  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/tally.md'>tally(value, value, ...)</a></td><td> counts times values are seen, including as a set   </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/total_lines.md'>total_lines()</a></td><td> returns the number of rows in the file being scanned   </td></tr>
<tr><td>
    <a name="strings">
    Strings   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>concat(value, value, ...)</a> </td><td> joins any number of values                 </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>length(value)</a>             </td><td> returns the length of the value                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>lower(value)</a>              </td><td> makes a value lowercase                                     </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/metaphone.md'>metaphone(value, value)</a>  </td><td> returns the metaphone transformation of a string or does a reference look up </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>min_length(value)</a> and <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>max_length(value)</a>  </td><td> returns the length of the value                           </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>starts_with(value, value)</a>   </td><td> checks if the first value starts with the second    </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>strip(value)</a>              </td><td> trims off whitespace     </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>substring(value, int)</a>     </td><td> returns the first n chars from the value                  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/string_functions.md'>upper(value)</a>              </td><td> makes a value uppercase                                     </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/regex.md'>regex(regex-string, value)</a> and <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/regex.md'>exact(regex-string, value)</a> </td><td> match on a regular expression </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/jinja.md'>jinja(value, value)</a>  </td><td> applies a Jinja2 template                           </td></tr>

<tr><td>
    <a name="headers">
    Headers   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/end.md'>end(int)</a>                         </td><td> returns the value of the last header value                      </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/header_name.md'>header_name(value, value)</a> and <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/header_name.md'>header_index(value, value)</a> </td><td> returns header name for an index or index for a name      </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/variables_and_headers.md'>headers(value)</a>  </td><td> indicates to another function that it should look in headers.      </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/header_names_mismatch.md'>header_names_mismatch(value)</a>  </td><td> checks the headers against a delimited list of expected headers   </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/count_headers.md'>count_headers()</a> and <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/count_headers.md'>count_headers_in_line()</a>    </td><td> returns the number of headers expected or the number found in the line      </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/reset_headers.md'>reset_headers()</a>  </td><td> sets the headers to the values of the current line      </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/mismatch.md'>mismatch()</a>  </td><td> returns the difference in number of value vs. number of headers      </td></tr>

<tr><td>
    <a name="misc">
Misc     </td><td>                               </td><td>                                                           </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/advance.md'>advance(int)</a></td><td> skips the next n-rows </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/after_blank.md'>after_blank()</a></td><td> matches when a line was preceded by a blank line </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/collect.md'>collect(value, ...)</a></td><td> identifies the headers to collect when a row matches </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/get.md'>get(value, value)</a></td><td> gets a varible value </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/last.md'>firstline()</a></td><td> matches on the 0th line, if scanned </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/last.md'>firstscan()</a></td><td> matches on the 1st line scanned </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/last.md'>firstmatch()</a></td><td> matches on the 1st line matched </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/last.md'>last()</a></td><td> true on the last row that will be scanned </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/import.md'>import()</a></td><td> inject another csvpath into the current csvpath </td></tr>


<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/now.md'>now(format)</a></td><td> a datetime, optionally formatted       </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/date.md'>date(value, format)</a></td><td> a date parsed according to a format string  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/date.md'>datetime(value, format)</a></td><td> a datetime parsed according to a format string  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/has_dups.md'>has_dups(header, ...)</a>,
<a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/has_dups.md'>count_dups(header, ...)</a>, and
<a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/has_dups.md'>dup_lines(header, ...)</a>
</td><td> these functions track duplicate lines  </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/print.md'>print(str, value)</a></td><td> prints the interpolated string  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/print_line.md'>print_line(value,value)</a></td><td> prints the current line unchanged  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/print_line.md'>print_queue(value,value)</a></td><td> returns the number of strings printed  </td></tr>
<tr><td>           </td><td> random(starting, ending)      </td><td> generates a random int from starting to ending            </td>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/pop.md'>push(name, value)</a> </td><td> pushes a value on a stack    </td>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/pop.md'>pop(name)</a> </td><td> pops a value off a stack    </td>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/pop.md'>peek(name, int)</a> </td><td> accesses a value at an index in a stack    </td>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/pop.md'>peek_size(name)</a> </td><td> returns the size of a stack    </td>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/pop.md'>stack(name)</a> </td><td> returns a variable that is stack of values that were pushed   </td>


<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/replace.md'>replace(value, value)</a> </td><td> replaces a header value with another value   </td>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/stop.md'>skip(value)</a> </td><td> skips to the next line scanned if a condition is met   </td>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/stop.md'>stop(value)</a> </td><td> stops path scanning if a condition is met                 </td>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/track.md'>track(value, value)</a> </td><td> tracks a value by name             </td>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/no.md'>none()</a>                    </td><td> returns None </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/docs/functions/variables_and_headers.md'>variables()</a>    </td><td> indicates to another function that it should look in the variables       </td></tr>
</tr>
</table>

