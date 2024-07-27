from csvpath import CsvPath


class Main:
    @classmethod
    def do_path(self):
        pathstr = """$/Users/davidkershaw/Desktop/csvs/exportedLogRecords.CSV
                [*][
                   @col20 = substring(#20, 40)
                   count_lines()==0 -> print( "error, line, level, message" )
                   regex(#20, /InvocationContext/) ->
                     print("$.variables.col20, $.line_count, $.headers.level, $.headers.message" )
                ]
                """
        # /InvocationContext/
        path = CsvPath()
        path.parse(pathstr)
        path.fast_forward()


if __name__ == "__main__":
    main = Main()
    main.do_path()

    """
                                print(yes(), " THIS IS A MATCH  $.name\n
                                             delimiter: $.delimiter \n
                                             quotechar: $.quotechar \n
                                             match count: $.match_count\n
                                             line count: $.line_count\n
                                             scan count: $.scan_count\n
                                             headers.city: $.headers.city\n
                                             headers: $.headers\n
                                             variables: $.variables\n
                                             variables.test: $.variables.test\n
                                             scan part: $.scan_part\n\n\n "
    """
