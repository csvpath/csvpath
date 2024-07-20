from csvpath.csvpath import CsvPath

# pathstr = f'${filepath}[*][#statecode="MA"]'
# pathstr = f'${filepath}[*][#statecode="MA" first(#city, #statecode)]'
# pathstr = f'${filepath}[4000-5000+22949][@test=#4 count(in(#statecode,"LA|MA|CT"))=12]'


class Main:
    @classmethod
    def do_path(self):
        pathstr = """$/Users/davidkershaw/Desktop/csvs/exportedLogRecords.CSV
                        [1*][
                        @col20 = substring( #20, 45 )
                        @cntln = count_lines()
                        print(
                            regex(#20, /InvocationContext/),
                            " $.variables.col20, $.variables.cntln, $.headers.level, $.headers.message" )

                    ]"""

        path = CsvPath()
        path.parse(pathstr)
        line = "______"
        for line in path.next():
            pass
            # print(f"line: {line}")

        print(f"variables: {path.variables}")
        # print(f"headers: {path.headers}")
        """
        for i, h in enumerate(path.headers):
            v = None
            try:
                v = f"{line[i]}"[0:20]
            except:
                pass
            # print(f"{i}: {h} = {v}")
        """


if __name__ == "__main__":

    """
                            regex(#message, /InvocationContext/)


    import cProfile
        cProfile.run("Main.do_path()", sort="cumtime")
    """

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
