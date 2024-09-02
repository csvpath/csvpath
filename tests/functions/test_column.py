import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsColumn(unittest.TestCase):
    """
    def test_function_column(self):
        path = CsvPath()
        Save._save(path, "test_function_column")
        path.parse(
            f""
            ${PATH}[*]
            [
                @i = column("firstname")
                @j = column("lastname")
                @n = column(2)
                @m = column(minus(1))
            ]""
        )
        lines = path.collect()
        print(f"test_function_column: path vars: {path.variables}")
        assert len(lines) == 9
        assert path.variables["j"] == 1
        assert path.variables["i"] == 0
        assert path.variables["n"] == "say"
        assert path.variables["m"] == "lastname"
    """

    def test_function_header_name_and_index1(self):
        path = CsvPath()
        Save._save(path, "test_function_header_name_and_index1")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = header_index("firstname")
                @j = header_index("lastname", 1)
                @k = header_index("say", 0)
                @l = header_index("foobar", 1)
                @m = header_index("foobar")
                @n = header_name(minus(1))
                @o = header_name(2)
                @p = header_name(0, "firstname")
                @q = header_name(2, "firstname")
                @r = header_name(4)
                @s = header_name(0, "ffirstname")
            ]"""
        )
        path.collect()
        print(f"test_function_header_name_and_index1: path vars: {path.variables}")
        assert path.variables["i"] == 0
        assert path.variables["j"] is True
        assert path.variables["k"] is False
        assert path.variables["l"] is False
        assert path.variables["m"] is None
        assert path.variables["n"] == "lastname"
        assert path.variables["o"] == "say"
        assert path.variables["p"] is True
        assert path.variables["q"] is False
        assert path.variables["r"] is None
        assert path.variables["s"] is False

    def test_function_header_name_and_index2(self):
        path = CsvPath()
        Save._save(path, "test_function_header_name_and_index2")
        path.parse(
            f""" ${PATH}[2][
                header_index("firstname")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_header_name_and_index2: lines: {lines}")
        assert len(lines) == 1

    def test_function_header_name_and_index3(self):
        path = CsvPath()
        Save._save(path, "test_function_header_name_and_index3")
        path.parse(
            f""" ${PATH}[2][
                not( header_name(4) )
            ]"""
        )
        lines = path.collect()
        print(f"test_function_header_name_and_index3: lines: {lines}")
        assert len(lines) == 1

    def test_function_header_name_and_index4(self):
        path = CsvPath()
        Save._save(path, "test_function_header_name_and_index4")
        path.parse(
            f""" ${PATH}[2][
                header_name(0, "firstname")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_header_name_and_index4: lines: {lines}")
        assert len(lines) == 1

    def test_function_header_name_and_index5(self):
        path = CsvPath()
        Save._save(path, "test_function_header_name_and_index5")
        path.parse(
            f""" ${PATH}[2][
                header_name(0, "ffirstname")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_header_name_and_index5: lines: {lines}")
        assert len(lines) == 0

    def test_function_header_names_mismatch1(self):
        path = CsvPath()
        Save._save(path, "test_function_header_names_mismatch1")
        path.parse(
            f""" ${PATH}[2][
                header_names_mismatch.chk("firstname|lastname|say")
                header_names_mismatch.more("firstname|lastname|say|more")
                header_names_mismatch.order("lastname|firstname|say")
                header_names_mismatch.dup("firstname|firstname|say")
                header_names_mismatch.short("firstname|say")
            ]"""
        )
        path.collect()
        print(f"test_function_header_names_mismatch1: vars: {path.variables}")
        v = path.variables
        assert len(v["chk_present"]) == 3
        assert len(v["more_present"]) == 3
        assert len(v["order_present"]) == 1
        assert len(v["dup_present"]) == 2
        assert len(v["short_present"]) == 1

        assert len(v["chk_unmatched"]) == 0
        assert len(v["more_unmatched"]) == 1
        assert len(v["order_unmatched"]) == 0
        assert len(v["dup_unmatched"]) == 1
        assert len(v["short_unmatched"]) == 1

        assert len(v["chk_misordered"]) == 0
        assert len(v["more_misordered"]) == 0
        assert len(v["order_misordered"]) == 2
        assert len(v["dup_misordered"]) == 1
        assert len(v["short_misordered"]) == 1

        assert len(v["chk_duplicated"]) == 0
        assert len(v["more_duplicated"]) == 0
        assert len(v["order_duplicated"]) == 0
        assert len(v["dup_duplicated"]) == 1
        assert len(v["short_duplicated"]) == 0
