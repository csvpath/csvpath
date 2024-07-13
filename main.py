from csvpath.csvpath import CsvPath

# pathstr = f'${filepath}[*][#statecode="MA"]'
# pathstr = f'${filepath}[*][#statecode="MA" first(#city, #statecode)]'
# pathstr = f'${filepath}[4000-5000+22949][@test=#4 count(in(#statecode,"LA|MA|CT"))=12]'


class Main:
    @classmethod
    def do_path(self):
        pathstr = """$/Users/davidkershaw/Desktop/csvs/pipe_delimited.csv
                        [1*]
                        [
                            @code=#statecode
                            @test=count(in(#statecode,"LA|MA|CT"))
                            print(no(), " THIS IS A MATCH  $.name\n
                                             delimiter: $.delimiter \n
                                             quotechar: $.quotechar \n
                                             match count: $.match_count\n
                                             line count: $.line_count\n
                                             scan count: $.scan_count\n
                                             headers: $.headers\n
                                             scan part: $.scan_part\n
                                             the test var: $.variables.test\n\n\n")
                        ]"""

        path = CsvPath(delimiter="|")
        path.parse(pathstr)
        print("calling next")
        for line in path.next():
            # print(f"line: {line}")
            pass
        print("done with next")
        print(f"path vars: {path.variables}")


if __name__ == "__main__":

    """
    import cProfile
    cProfile.run("Main.do_path()", sort="cumtime")
    """

    main = Main()
    main.do_path()
