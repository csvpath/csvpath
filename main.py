from csvpath import CsvPath


class Main:
    @classmethod
    def do_path(self):
        pathstr1 = """$/Users/davidkershaw/Desktop/csvs/exportedLogRecords.CSV
                [*][
                   @col20 = substring(#20, 40)
                   count_lines()==0 -> print( "time, error, line, level, message" )
                   regex(#20, /InvocationContext/) ->
                     print("$.rows_time, $.variables.col20, $.line_count, $.headers.level, $.headers.message" )
                     last() -> print("Checked $.total_lines total lines in $.rows_time ms.,,,,")
                ]
                """
        pathstr1 = pathstr1
        pathstr2 = """
        $tests/test_resources/test.csv[*][
            @failed = equals(#firstname, "Frog")
            @failed.asboo<D-r><D-r>l -> print("Error: Check line $.line_count for a row with the name Frog")
        ] """
        pathstr2 = pathstr2

        path = CsvPath()
        # path.parse(pathstr1)
        path.parse(pathstr2)
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
