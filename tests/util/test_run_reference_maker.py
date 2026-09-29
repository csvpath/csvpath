import unittest
from csvpath.util.run_reference_maker import RunReferenceMaker

CRT = "2026-01-01_00-00-00"


class TestUtilRunReferenceMaker(unittest.TestCase):
    def test_util_run_reference_maker_1(self) -> None:
        assert (
            RunReferenceMaker.run_reference(
                archive="animals", pathsname="local", crt=CRT
            )
            == f"$local.results.{CRT}"
        )

    def test_util_run_reference_maker_2(self) -> None:
        assert (
            RunReferenceMaker.run_reference(
                archive="/data/archive",
                pathsname="orders",
                crt=f"/data/archive/orders/x/y/{CRT}",
            )
            == f"$orders.results.x/y/{CRT}"
        )

    def test_util_run_reference_maker_3(self) -> None:
        assert (
            RunReferenceMaker.run_reference(
                archive="data/archive",
                pathsname="orders",
                crt=f"/Users/dk/data/archive/orders/x/y/{CRT}",
            )
            == f"$orders.results.x/y/{CRT}"
        )

    def test_util_run_reference_maker_4(self) -> None:
        assert (
            RunReferenceMaker.run_reference(
                archive="/data/archive",
                pathsname="$orders.csvpaths.0:from",
                crt=f"/data/archive/orders/x/y/{CRT}",
            )
            == f"$orders.results.x/y/{CRT}"
        )
