import os
from uuid import UUID
import unittest
from csvpath import CsvPath

UUIDS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}uuid.csv"


class TestCsvPathFunctionsUuid(unittest.TestCase):
    def test_function_uuid_1(self):
        path = CsvPath().parse(
            f"""${UUIDS}[1*][
            @v = uuid( #0 )
            push( "uuid", @v )
            ]"""
        )
        path.collect()
        u = path.variables["uuid"]
        assert u == [True, False, True]

    def test_function_uuid_2(self):
        path = CsvPath().parse(
            f"""~ validation-mode:print, no-raise~ ${UUIDS}[1*][
            @v = uuid.notnone( #0 )
            push( "uuid", @v )
            ]"""
        )
        path.collect()
        u = path.variables["uuid"]
        assert u == [True, False, None]

    def test_function_uuid_3(self):
        path = CsvPath().parse(
            f"""${UUIDS}[1*][
            @v = uuid()
            push( "uuid", @v )
            ]"""
        )
        path.collect()
        u = path.variables["uuid"]
        for _ in u:
            assert isinstance(_, UUID)

    def test_function_uuid_4(self):
        path = CsvPath().parse(
            f"""~ validation-mode:print, no-raise~ ${UUIDS}[1*][
                line(
                    uuid(#0),
                    string(#1)
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 2

    def test_function_uuid_5(self):
        path = CsvPath().parse(
            f"""~ validation-mode:print, no-raise~ ${UUIDS}[1*][
                line(
                    uuid.notnone(#0),
                    string(#1)
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
