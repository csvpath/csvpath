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
                            print(#statecode=="MA", " THIS IS A MATCH  $.name\n
                                             $.delimiter \n
                                             $.quotechar \n
                                             $.match_count\n
                                             $.line_count\n
                                             $.scan_count\n
                                             $.line\n
                                             $.match_json\n
                                             $.expressions\n
                                             $.headers\n
                                             $.scan_part\n
                                             $.match_part\n
                                             $.variables\n\n\n")
                        ]"""

        path = CsvPath(delimiter="|")
        path.verbose(True)
        path.parse(pathstr)
        matched = 0
        for i, line in enumerate(path.next()):
            matched += 1

        print(f"path vars: {path.variables}")
        print(f"matched: {matched}")


if __name__ == "__main__":

    """
    import cProfile
    cProfile.run("Main.do_path()", sort="cumtime")
    """

    main = Main()
    main.do_path()
