import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsNor(unittest.TestCase):
    def test_function_nor_1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                @c = count.frogbats(
                    and(
                        #firstname == "Frog",
                        #lastname == "Bat"
                    )
                )
                @c2 = count.notfrogbats(
                    nor(
                        #firstname == "Frog",
                        #lastname == "Bat"
                    )
                )

            ]"""
        )
        path.collect()
        fb = path.variables.get("frogbats")
        nfb = path.variables.get("notfrogbats")
        print(f"{path.variables}")
        # there are two Frog Bats
        assert fb == {False: 7, True: 2}
        # there are two non-Frog, non-Bats
        assert nfb == {False: 7, True: 2}

    def test_function_nor_2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                nor( yes(), yes(), yes() ) ->
                    @check1 = false()
                nor( no(), no(), no() ) ->
                    @check2 = true()
                @check3 = nor( no(), last() )
                push("check3s", @check3)

            ]"""
        ).fast_forward()

        assert "check1" not in path.variables
        assert "check2" in path.variables
        assert "check3" in path.variables
        assert "check3s" in path.variables

        assert path.variables["check2"] is True
        assert path.variables["check3"] is False
        assert len(path.variables["check3s"]) == 9
        assert path.variables["check3s"] == [
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            False,
        ]

    # ==============================

    def test_function_nand_1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                @c = count.frogbats(
                    and(
                        #firstname == "Frog",
                        #lastname == "Bat"
                    )
                )
                @c2 = count.notfrogbats(
                    nand(
                        #firstname == "Frog",
                        #lastname == "Bat"
                    )
                )

            ]"""
        )
        path.collect()
        fb = path.variables.get("frogbats")
        nfb = path.variables.get("notfrogbats")
        print(f"{path.variables}")
        # there are two Frog Bats
        assert fb == {False: 7, True: 2}
        # there are two non-Frog, non-Bats
        assert nfb == {False: 2, True: 7}

    def test_function_nand_2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                @check1 = nand( yes(), yes(), yes() )
                @check2 = nand( no(), no(), no() )
                @check3 = nand( no(), last() )
                push("check3s", @check3)

            ]"""
        ).fast_forward()

        assert "check1" in path.variables
        assert "check2" in path.variables
        assert "check3" in path.variables
        assert "check3s" in path.variables

        assert path.variables["check1"] is False
        assert path.variables["check2"] is True
        assert path.variables["check3"] is True
        assert len(path.variables["check3s"]) == 9
        assert path.variables["check3s"] == [
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
        ]
