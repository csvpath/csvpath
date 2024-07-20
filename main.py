from csvpath.csvpath import CsvPath


class Main:
    @classmethod
    def do_path(self):
        pathstr = """$/Users/davidkershaw/Desktop/csvs/exportedLogRecords.CSV
                        [*][
                            @col20 = substring( #20, 50 )
                            @cntln = count_lines()
                            print( count_lines() == 0, "error, line, level, message")
                            print( regex(#20, /InvocationContext/),
                                "$.variables.col20, $.variables.cntln, $.headers.level, $.headers.message" )
                        ]
                  """

        path = CsvPath()
        path.parse(pathstr)
        for line in path.next():
            pass


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
