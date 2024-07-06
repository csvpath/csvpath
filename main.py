from csvpath.csvpath import CsvPath
import sys

        #pathstr = f'${filepath}[*][#statecode="MA"]'
        #pathstr = f'${filepath}[*][#statecode="MA" first(#city, #statecode)]'
        #pathstr = f'${filepath}[4000-5000+22949][@test=#4 count(in(#statecode,"LA|MA|CT"))=12]'


class Repl():

    def __init__(self):
        self.filepath = "tests/test_resources/test.csv"


    def take_input(self):
        while ( True ):
            resp = self._input( ">> ")
            if not resp or resp.strip() == '':
                continue
            self.do_path(resp)


    def _response(self, text:str) -> None:
        sys.stdout.write(f"\033[92m {text}\033[0m\n")

    def _input(self, prompt:str) -> str:
        try:
            response = input(f"{prompt}\033[93m")
            sys.stdout.write("\033[0m")
            return response.strip()
        except KeyboardInterrupt:
            return "quit"


    def do_path(self, pathstr):
        path = CsvPath(delimiter=",")
        path.verbose(True)
        scanner = path.parse(pathstr)
        for i, line in enumerate( path.next() ):
            self._response(line)

        print(f"path vars: {path.variables}")


if __name__ == "__main__":
    repl = Repl()
    repl.take_input()

