
# Functions

Functions perform work within a csvpath. A function is represented by a name followed by parentheses.

There are dozens of functions that are outlined elsewhere. More functions can be easily created; although, at the moment there is not yet a simple way to incorporate external code as a new function without changing the CsvPath codebase.

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
Qualifiers are described elsewhere.

# Examples
- `not(count()==2)`
- `add( 5, 3, 1 )`
- `concat( end(), regex(#0, /[0-5]+abc/))`


## All the functions

Most of the work of matching is done in functions. The match functions are the following.


<table>
<tr><th> Group     </th><th>Function                       </th><th> What it does                                              </th></tr>
<tr><td> Boolean   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/any.md'>any(value, value)</a>  </td><td> existence test across a range of places </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/no.md'>no()</a>  </td><td> always false                                  </td></tr>
<tr><td>           </td><td> not(value)                    </td><td> negates a value                                           </td></tr>
<tr><td>           </td><td> or(value, value,...)          </td><td> match any one                                             </td></tr>
<tr><td>           </td><td> yes()                         </td><td> always true                                               </td></tr>
<tr><td>           </td><td> exists(value)    </td><td> tests if the value exists            </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/in.md'>in(value, list)</a>  </td><td> match in a pipe-delimited list    </td></tr>
<tr><td> Math      </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> add(value, value, ...)        </td><td> adds numbers                                              </td></tr>
<tr><td>           </td><td> divide(value, value, ...)     </td><td> divides numbers                                           </td></tr>
<tr><td>           </td><td> multiply(value, value, ...)   </td><td> multiplies numbers                                        </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/subtract.md'>subtract(value, value, ...)</a> or minus(int)    </td><td> subtracts numbers or makes a number negative                                        </td></tr>
<tr><td>           </td><td> after(value)                  </td><td> finds things after a date, number, string                 </td></tr>
<tr><td>           </td><td> before(value)                 </td><td> finds things before a date, number, string                </td></tr>
<tr><td> Stats     </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/average.md'>average(number, type)</a> </td><td> returns the average up to current "line", "scan", "match" </td></tr>
<tr><td>           </td><td> median(value, type)           </td><td> median value up to current "line", "scan", "match"        </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/max.md'>max(value, type)</a> </td><td> largest value seen up to current "line", "scan", "match"  </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/max.md'>min(value, type)</a></td><td> smallest value seen up to current "line", "scan", "match" </td></tr>
<tr><td>           </td><td> percent(type)                 </td><td> % of total lines for "scan", "match", "line"              </td></tr>
<tr><td> Counting  </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/count.md'>count()</a> </td><td> counts the number of matches            </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/count.md'>count(value)</a> </td><td> count matches of value              </td></tr>
<tr><td>           </td><td> count_lines()                 </td><td> count lines to this point in the file                     </td></tr>
<tr><td>           </td><td> count_scans()                 </td><td> count lines we checked for match                          </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/first.md'>first(value, value, ...)</a> </td><td> match the first occurrence and capture line  </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/increment.md'>increment(value, n)</a> </td><td> increments a variable by n each time seen   </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/every.md'>every(value, number)</a> </td><td> match every Nth time a value is seen  </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/tally.md'>tally(value, value, ...)</a></td><td> counts times values are seen, including as a set   </td></tr>
<tr><td> Strings   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> concat(value, value)          </td><td> joins two values                 </td></tr>
<tr><td>           </td><td> length(value)                 </td><td> returns the length of the value                           </td></tr>
<tr><td>           </td><td> lower(value)                  </td><td> makes value lowercase                                     </td></tr>
<tr><td>           </td><td> regex(regex-string, value)    </td><td> match on a regular expression                             </td></tr>
<tr><td>           </td><td> substring(value, int)         </td><td> returns the first n chars from the value                  </td></tr>
<tr><td>           </td><td> upper(value)                  </td><td> makes value uppercase                                     </td></tr>
<tr><td> Columns   </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/end.md'>end(int)</a>                         </td><td> returns the value of the last column                      </td></tr>
<tr><td>           </td><td> column(value)                 </td><td> returns column name for an index or index for a name      </td></tr>
<tr><td> Other     </td><td>                               </td><td>                                                           </td></tr>
<tr><td>           </td><td> header()                      </td><td> indicates to another function to look in headers       </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/now.md'>now(format)</a></td><td> a datetime, optionally formatted       </td></tr>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/print.md'>print(value, str)</a></td><td> when matches prints the interpolated string  </td></tr>
<tr><td>           </td><td> random(starting, ending)      </td><td> generates a random int from starting to ending            </td>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/stop.md'>stop(value)</a> </td><td> stops path scanning if a condition is met                 </td>
<tr><td>           </td><td> <a href='../csvpath/matching/functions/when.md'>when(value, value)</a> </td><td> activate a value when a condition matches   </td>
<tr><td>           </td><td> variable()                    </td><td> indicates to another function to look in variables       </td></tr>
</tr>
</table>

