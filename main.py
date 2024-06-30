from csvpath.csvpath import CsvPath

#filepath = "tests/test_resources/test.csv"

filepath = '/Users/davidkershaw/Desktop/csvs/pipe_delimited.csv'

def one():
    path = CsvPath(delimiter="|")
    pathstr = f'${filepath}[4000-5000+22949][@test=#4 count(in(#statecode,"LA|MA|CT"))=12]'


    #print(pathstr)
    result = path.parse(pathstr)
    #print(f"{result}")

    for i, line in enumerate( path.next() ):
        print(f" {path.current_line_number()} {i}: {line}")

    print(f"path vars: {path.variables}")


if __name__ == "__main__":
    one()


