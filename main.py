from csvpath.csvpath import CsvPath

# pathstr = f'${filepath}[*][#statecode="MA"]'
# pathstr = f'${filepath}[*][#statecode="MA" first(#city, #statecode)]'
# pathstr = f'${filepath}[4000-5000+22949][@test=#4 count(in(#statecode,"LA|MA|CT"))=12]'


from cProfile import Profile
from pstats import SortKey, Stats


class Main:
    @classmethod
    def do_path(self):
        pathstr = """$/Users/davidkershaw/Desktop/csvs/pipe_delimited.csv
                        [4000-5000]
                        [@test=#4 count( in(#statecode,"LA|MA|CT") )]"""

        path = CsvPath(delimiter=",")
        path.verbose(True)
        path.parse(pathstr)
        for i, line in enumerate(path.next()):
            pass

        print(f"path vars: {path.variables}")


if __name__ == "__main__":

    import cProfile

    cProfile.run("Main.do_path()", sort="cumtime")

    """
    with Profile() as profile:
        cProfile.run('main()')
        print(f"{Main.do_path() = }")(
            Stats(profile)
            .strip_dirs()
            .sort_stats(SortKey.CALLS)
            .print_stats()
        )
    """

    # main = Main()
    # main.do_path()
