import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestValidBasicTypes(unittest.TestCase):
    def test_validity_int1(self):
        path = CsvPath()
        Save._save(path, "test_validity_int1")
        path.parse(
            f"""${PATH}[*][
                int.notnone(none())
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_validity_int2(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_validity_int2")
        path.parse(
            f""" ~id:test_validity_none2~
                ${"tests/test_resources/test.csv"}[*][
                    any( length( concat("a", int(random(0)))))
                ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_validity_int3(self):
        path = CsvPath()
        Save._save(path, "test_validity_int3")
        path.parse(
            f"""~id:validity_int3~ ${PATH}[*][
                int.notnone("a")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_validity_date1(self):
        path = CsvPath()
        Save._save(path, "test_validity_date1")
        path.parse(
            f"""~id:validity_date1~ ${PATH}[*][
                date()
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_validity_date2(self):
        path = CsvPath()
        Save._save(path, "test_validity_date2")
        path.parse(
            f"""~id:validity_date2~ ${PATH}[*][
                date.notnone(none())
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_validity_date3(self):
        path = CsvPath()
        Save._save(path, "test_validity_date3")
        path.parse(
            f"""~id:validity_date3~ ${PATH}[*][
                date("2024-01-01")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_date4(self):
        path = CsvPath()
        Save._save(path, "test_validity_date4")
        path.parse(
            f"""~id:validity_date4~ ${PATH}[*][
                @d = date("2024-01-01")
                date(@d)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_date5(self):
        path = CsvPath()
        Save._save(path, "test_validity_date5")
        path.parse(
            f"""~id:validity_date5~ ${PATH}[*][
                date("the 3rd of feb")
            ]"""
        )
        with pytest.raises(ChildrenException):
            lines = path.collect()
            assert len(lines) == 0

    def test_validity_date6(self):
        path = CsvPath()
        Save._save(path, "test_validity_date6")
        path.parse(
            f"""~id:validity_date6~ ${PATH}[*][
                date("the 3rd of feb", "%Y")
            ]"""
        )
        with pytest.raises(ValueError):
            lines = path.collect()
            assert len(lines) == 0

    def test_validity_now1(self):
        path = CsvPath()
        Save._save(path, "test_validity_now2")
        path.parse(
            f"""~id:validity_now1~ ${PATH}[*][
                now("%Y")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_now2(self):
        path = CsvPath()
        Save._save(path, "test_validity_now2")
        path.parse(
            f"""~id:validity_now2~ ${PATH}[*][
                today("%Y")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.collect()
            # assert len(lines) == 0

    def test_validity_now3(self):
        path = CsvPath()
        Save._save(path, "test_validity_now3")
        path.parse(
            f"""~id:validity_now3~ ${PATH}[*][
                now()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_now4(self):
        path = CsvPath()
        Save._save(path, "test_validity_now4")
        path.parse(
            f"""~id:validity_now4~ ${PATH}[*][
                now("2024-01-01","%Y")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.collect()

    def test_validity_none1(self):
        path = CsvPath()
        Save._save(path, "test_validity_none")
        path.parse(
            f"""~id:validity_none1~ ${PATH}[*][
                none("2024-01-01")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.collect()

    def test_validity_none2(self):
        path = CsvPath()
        Save._save(path, "test_validity_none2")
        path.parse(
            f"""~id:validity_none2~ ${PATH}[*][
                none(none())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_none3(self):
        path = CsvPath()
        Save._save(path, "test_validity_none3")
        path.parse(
            f"""~id:validity_none3~ ${PATH}[*][
                none(-1)
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.collect()

    def test_validity_none4(self):
        path = CsvPath()
        Save._save(path, "test_validity_none4")
        path.parse(
            f"""~id:validity_none4~ ${PATH}[*][
                none(5, 9)
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.collect()

    def test_validity_none5(self):
        path = CsvPath()
        Save._save(path, "test_validity_none5")
        path.parse(
            """~id:validity_none5~ $tests/test_resources/food.csv[*][
                none(#3)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_string1(self):
        path = CsvPath()
        Save._save(path, "test_function_string1")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_string2(self):
        path = CsvPath()
        Save._save(path, "test_function_string2")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 25, 0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_string3(self):
        path = CsvPath()
        Save._save(path, "test_function_string2")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 0, 25)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_string4(self):
        path = CsvPath()
        Save._save(path, "test_function_string4")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_string5(self):
        path = CsvPath()
        Save._save(path, "test_function_string5")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 25)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_string6(self):
        path = CsvPath()
        Save._save(path, "test_function_string6")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 5)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_string7(self):
        path = CsvPath()
        Save._save(path, "test_function_string7")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 0, 25, 9)
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.collect()
