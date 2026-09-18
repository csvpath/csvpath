import unittest
import os
from csvpath import CsvPath
from csvpath.util.file_readers import DataFileReader

SCHEMA = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}animals.schema.json"
SCHEMA_LIST = (
    f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}animals_list.schema.json"
)


class TestCsvPathDynamic(unittest.TestCase):
    def test_csvpath_dynamic_1(self):
        jsonl = [
            {"a": "fish", "b": "gull", "c": "clam"},
            {"a": "ant", "b": "mouse", "c": "dog"},
            {"a": "elephant", "b": "tiger", "c": "snake"},
        ]
        DataFileReader.register_data(path="dynamictest", data=jsonl, shape="jsonl")
        c = """
            ~
              validation-mode: no-raise, print
            ~
            $dynamictest[*][
                print_line()
                header_table()
                line(
                    string.notnone(#a),
                    string.notnone(#b),
                    string(#c)
                )
                #a == "ant"
            ] """
        lines = CsvPath().collect(c)
        assert len(lines) == 1
        #
        # clear the box. in this case not needed, but good practice.
        #
        DataFileReader.deregister_data("dynamictest", shape="jsonl")

    def test_csvpath_dynamic_2(self):
        jsonl = [
            ["fish", "gull", "clam"],
            ["ant", "mouse", "dog"],
            ["elephant", "tiger", "snake"],
        ]
        DataFileReader.register_data(path="dynamictest", data=jsonl, shape="jsonl")
        c = """
            ~
              validation-mode: no-raise, print
            ~
            $dynamictest[*][
                print_line()
                header_table()
                line(
                    string.notnone(#0),
                    string.notnone(#1),
                    string(#2)
                )
                #0 == "ant"
            ] """
        lines = CsvPath().collect(c)
        assert len(lines) == 1
        DataFileReader.deregister_data("dynamictest", shape="jsonl")

    def test_csvpath_dynamic_3(self):
        js = {
            "ocean": ["fish", "lobster", "clam"],
            "insect": ["ant", "spider", "flea"],
            "land": ["elephant", "tiger", "snake"],
        }
        DataFileReader.register_data(path="dynamictest", data=js, shape="json")
        c = f"""
            ~
              validation-mode: no-raise, print
            ~
            $dynamictest[*][
                jsonschema("{SCHEMA}")
            ] """
        lines = CsvPath().collect(c)
        print(f"lines: {lines}")
        assert len(lines) == 1
        DataFileReader.deregister_data("dynamictest", shape="json")

    def test_csvpath_dynamic_4(self):
        js = {
            "sky": ["bluebird", "bluejay", "blue-footed boobie"],
            "insect": ["ant", "spider", "flea"],
            "land": ["elephant", "tiger", "snake"],
        }
        DataFileReader.register_data(path="dynamictest", data=js, shape="json")
        c = f"""
            ~
              validation-mode: no-raise, print
            ~
            $dynamictest[*][
                jsonschema("{SCHEMA}")
            ] """
        lines = CsvPath().collect(c)
        print(f"lines: {lines}")
        assert len(lines) == 0
        DataFileReader.deregister_data("dynamictest", shape="json")

    def test_csvpath_dynamic_5(self):
        js = [
            {
                "sky": ["bluebird", "bluejay", "blue-footed boobie"],
                "insect": ["ant", "spider", "flea"],
                "land": ["elephant", "tiger", "snake"],
            },
            {
                "ocean": ["fish", "lobster", "clam"],
                "insect": ["ant", "spider", "flea"],
                "land": ["elephant", "tiger", "snake"],
            },
            {
                "below": ["mole", "badger", "worm"],
                "insect": ["ant", "spider", "flea"],
                "land": ["elephant", "tiger", "snake"],
            },
        ]
        stmt = f"""
            ~ validation-mode: no-raise, print, fail ~
            $dynamictest[*][
                jsonschema("{SCHEMA}")
            ]
        """

        valid = 0
        path = None
        for _ in js:
            DataFileReader.register_data(path="dynamictest", data=_, shape="json")
            if path is None:
                path = CsvPath()
                path.parse(stmt)
            path.fast_forward()
            valid += 1 if path.is_valid else 0
            DataFileReader.deregister_data("dynamictest", shape="json")
            path.rewind()
        print(f"valid: {valid}")
        assert valid == 1

    def test_csvpath_dynamic_6(self):
        js = [
            {
                "sky": ["bluebird", "bluejay", "blue-footed boobie"],
                "insect": ["ant", "spider", "flea"],
                "land": ["elephant", "tiger", "snake"],
            },
            {
                "ocean": ["fish", "lobster", "clam"],
                "insect": ["ant", "spider", "flea"],
                "land": ["elephant", "tiger", "snake"],
            },
            {
                "below": ["mole", "badger", "worm"],
                "insect": ["ant", "spider", "flea"],
                "land": ["elephant", "tiger", "snake"],
            },
        ]
        stmt = f"""
            ~ validation-mode: no-raise, print, fail ~
            $dynamictest[*][
                jsonschema("{SCHEMA_LIST}")
            ]
        """

        valid = 0
        path = None
        DataFileReader.register_data(path="dynamictest", data=js, shape="json")
        if path is None:
            path = CsvPath()
            path.parse(stmt)
        path.fast_forward()
        valid += 1 if path.is_valid else 0
        DataFileReader.deregister_data("dynamictest", shape="json")
        print(f"valid: {valid}")
        assert valid == 1
