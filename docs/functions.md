
# Functions

Functions perform work within a csvpath. A function is represented by a name followed by parentheses.

There are dozens of functions listed below. More functions can be easily created.

Functions can contain:
- terms
- variables
- headers
- equality tests
- variable assignment
- other functions

Some functions take a specific or unlimited number of types as arguments.

Certain functions have qualifiers. An `onmatch` qualifier indicates that
the function should be applied only when the whole path matches.

Some functions optionally will make use of an arbitrary name qualifier to better name a tracking variable.
<a href='https://github.com/dk107dk/csvpath/blob/main/docs/qualifiers.md'>Read about qualifiers here.</a>

Creating your own function is easy. Once you create a function, you register it with the `FunctionFactory` class. You must register your functions each time you run CsvPath. Use your function in csvpaths by simply referring to it by name like any other function.

<a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/implementing_functions.md'>Read more about implementing your own functions here.</a>

# Examples
- `not(count()==2)`
- `add( 5, 3, 1 )`
- `concat( end(), regex(#0, /[0-5]+abc/))`


## All the functions

Most of the work of matching is done in functions. The match functions are the following.


<table>
<tr><th> Group     </th><th>Function                       </th><th> What it does                                              </th></tr>
<tr><td> Boolean   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/all.md'>all(value, value, ...)</a>  </td><td> existence test for all selected values or all headers </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/any.md'>any(value, value, ...)</a>  </td><td> existence test across a range of places </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/no.md'>no()</a>  </td><td> always false                                  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/not.md'>not(value)</a>                    </td><td> negates a value                                           </td></tr>
<tr><td>           </td><td> or(value, value,...)          </td><td> match any one                                             </td></tr>
<tr><td>           </td><td> yes()                         </td><td> always true                                               </td></tr>
<tr><td>           </td><td> empty(value)    </td><td> tests if the value is empty            </td></tr>
<tr><td>           </td><td> exists(value)    </td><td> tests if the value exists            </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/fail.md'>fail()</a>  </td><td> indicate that the CSV is invalid   </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/fail.md'>failed()</a></td><td> check if the CSV is invalid   </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/fail.md'>fail_and_stop()</a></td><td> stop the scan and declare the file invalid at the same time  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/fail.md'>valid()</a></td><td> check if the CSV is valid or invalid  </td></tr>


<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/in.md'>in(value, list)</a>  </td><td> match in a pipe-delimited list    </td></tr>
<tr><td> Math      </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> add(value, value, ...)        </td><td> adds numbers                                              </td></tr>
<tr><td>           </td><td> divide(value, value, ...)     </td><td> divides numbers                                           </td></tr>
<tr><td>           </td><td> multiply(value, value, ...)   </td><td> multiplies numbers                                        </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/subtract.md'>subtract(value, value, ...)</a>    </td><td> subtracts numbers or makes a number negative                                        </td></tr>
<tr><td>           </td><td> after(value, value) or gt(value, value) </td><td> finds things after a date, number, string        </td></tr>
<tr><td>           </td><td> before(value, value) or lt(value, value) </td><td> finds things before a date, number, string       </td></tr>
<tr><td> Stats     </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/average.md'>average(number, type)</a> </td><td> returns the average up to current "line", "scan", "match" </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/correlate.md'>correlate(value, value)</a> </td><td> gives the running correlation between two values </td></tr>
<tr><td>           </td><td> median(value, type)           </td><td> median value up to current "line", "scan", "match"        </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/max.md'>max(value, type)</a> </td><td> largest value seen up to current "line", "scan", "match"  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/max.md'>min(value, type)</a></td><td> smallest value seen up to current "line", "scan", "match" </td></tr>
<tr><td>           </td><td> percent(type)                 </td><td> % of total lines for "scan", "match", "line"              </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/percent_unique.md'>percent_unique(header)</a> </td><td> % of unique values found in the column  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/stdev.md'>stdev(stack)</a> and <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/stdev.md'>pstdev(stack)</a> </td><td> returns the standard deviation of numbers pushed on a stack  </td></tr>

<tr><td> Counting  </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/count.md'>count()</a> </td><td> counts the number of matches            </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/count.md'>count(value)</a> </td><td> count matches of value              </td></tr>
<tr><td>           </td><td> count_lines()                 </td><td> count lines to this point in the file                     </td></tr>
<tr><td>           </td><td> count_scans()                 </td><td> count lines we checked for match                          </td></tr>
<tr><td>           </td><td> count_headers()                 </td><td> returns the number of columns      </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/first.md'>first(value, value, ...)</a> </td><td> match the first occurrence and capture line  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/increment.md'>increment(value, n)</a> </td><td> increments a variable by n each time seen   </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/every.md'>every(value, number)</a> </td><td> match every Nth time a value is seen  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/tally.md'>tally(value, value, ...)</a></td><td> counts times values are seen, including as a set   </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/total_lines.md'>total_lines()</a></td><td> returns the number of rows in the file being scanned   </td></tr>
<tr><td> Strings   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/string_functions.md'>concat(value, value, ...)</a> </td><td> joins any number of values                 </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/string_functions.md'>length(value)</a>             </td><td> returns the length of the value                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/string_functions.md'>lower(value)</a>              </td><td> makes a value lowercase                                     </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/string_functions.md'>strip(value)</a>              </td><td> trims off whitespace     </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/string_functions.md'>substring(value, int)</a>     </td><td> returns the first n chars from the value                  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/string_functions.md'>upper(value)</a>              </td><td> makes a value uppercase                                     </td></tr>
<tr><td>           </td><td> regex(regex-string, value)    </td><td> match on a regular expression                             </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/jinja.md'>jinja(value, value)</a>  </td><td> applies a Jinja2 template                           </td></tr>

<tr><td> Columns   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/end.md'>end(int)</a>                         </td><td> returns the value of the last column                      </td></tr>
<tr><td>           </td><td> column(value)                 </td><td> returns column name for an index or index for a name      </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/header.md'>header(value)</a>  </td><td> indicates to another function to look in headers or tests if a header exists.      </td></tr>
<tr><td> Other     </td><td>                               </td><td>                                                           </td></tr>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/last.md'>firstline()</a></td><td> matches on the 0th line, if scanned </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/last.md'>firstscan()</a></td><td> matches on the 1st line scanned </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/last.md'>firstmatch()</a></td><td> matches on the 1st line matched </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/last.md'>last()</a></td><td> true on the last row that will be scanned </td></tr>


<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/now.md'>now(format)</a></td><td> a datetime, optionally formatted       </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/date.md'>date(value, format)</a></td><td> a date parsed according to a format string  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/date.md'>datetime(value, format)</a></td><td> a datetime parsed according to a format string  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/has_dups.md'>has_dups(header, ...)</a></td><td> matches when any row or set of headers have duplicate rows  </td></tr>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/print.md'>print(value, str)</a></td><td> when matches prints the interpolated string  </td></tr>
<tr><td>           </td><td> random(starting, ending)      </td><td> generates a random int from starting to ending            </td>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/pop.md'>push(name, value)</a> </td><td> pushes a value on a stack    </td>

<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/pop.md'>pop(name)</a> </td><td> pops a value off a stack    </td>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/pop.md'>peek(name, int)</a> </td><td> accesses a value at an index in a stack    </td>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/pop.md'>peek_size(name)</a> </td><td> returns the size of a stack    </td>
<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/pop.md'>stack(name)</a> </td><td> returns a variable that is stack of values that were pushed   </td>


<tr><td>           </td><td> <a href='https://github.com/dk107dk/csvpath/blob/main/csvpath/matching/functions/stop.md'>stop(value)</a> </td><td> stops path scanning if a condition is met                 </td>
<tr><td>           </td><td> variable()                    </td><td> indicates to another function to look in variables       </td></tr>
</tr>
</table>

