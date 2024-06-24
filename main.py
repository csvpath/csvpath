from csvpath.csvpath import CsvPath

filepath = "tests/test_resources/test.csv"

def one():
    path = CsvPath()
    pathstr = f"${filepath}[*]"
    print(pathstr)
    result = path.parse(pathstr)
    print(f"{result}")

    for ln in result.line_numbers():
        print(f"including line number: {ln}")

    for line in result.next():
        print(f"line: {line.strip()}")

def two():
    path = CsvPath()
    pathstr = f"${filepath}[2-4]"
    print(pathstr)
    result = path.parse(pathstr)
    print(f"{result}")

    for ln in result.line_numbers():
        print(f"including line number: {ln}")

    for line in result.next():
        print(f"line: {line.strip()}")

def three():
    path = CsvPath()
    pathstr = f"${filepath}[3*]"
    print(pathstr)
    result = path.parse(pathstr)
    print(f"{result}")

    for ln in result.line_numbers():
        print(f"including line number: {ln}")

    for line in result.next():
        print(f"line: {line.strip()}")

def four():
    path = CsvPath()
    pathstr = f"${filepath}[3]"
    print(pathstr)
    result = path.parse(pathstr)
    print(f"{result}")

    for ln in result.line_numbers():
        print(f"including line number: {ln}")

    for line in result.next():
        print(f"line: {line.strip()}")

def five():
    path = CsvPath()
    pathstr = f"${filepath}[1+3+5]"
    print(pathstr)
    result = path.parse(pathstr)
    print(f"{result}")

    for ln in result.line_numbers():
        print(f"including line number: {ln}")

    for line in result.next():
        print(f"line: {line.strip()}")

def six():
    path = CsvPath()
    result = path.parse("$[3]")
    print(f"{result}")

    for ln in result.line_numbers():
        print(f"including line number: {ln}")

    for line in result.next():
        print(f"line: {line.strip()}")

def seven():
    path = CsvPath()
    pathstr = f"${filepath}[4-2]"
    print(pathstr)
    result = path.parse(pathstr)
    print(f"{result}")

    for ln in result.line_numbers():
        print(f"including line number: {ln}")

    for line in result.next():
        print(f"line: {line.strip()}")



if __name__ == "__main__":
    #one()
    #two()
    #three()
    #four()
    #five()
    #six()
    seven()
