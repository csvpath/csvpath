import unittest
import os
import pytest
from typing import Callable

import pyarrow.parquet as pq
import pyarrow as pa
from pyarrow import DataType

from csvpath import CsvPath
from csvpath.matching.productions import Term, Equality
from csvpath.util.nos import Nos
from csvpath.matching.util.parquet_utility import ParquetUtility as paut
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.functions.function_factory import FunctionFactory as fact

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
TYPES = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}types4.csv"


class TestCsvPathFunctionsParquet(unittest.TestCase):
    def test_function_parquet_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise~
            ${PATH}[*]
            [
                parquet.person(
                    string.firstname(#0),
                    string.lastname(#1),
                    string.say(#2)
                )
            ]"""
        )
        path.fast_forward()
        path = os.path.join("parquet", "person.parquet")
        assert os.path.exists(path)

    def test_function_parquet_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise~
            ${PATH}[*]
            [
                parquet.person(
                    string.firstname(#0),
                    string.lastname(#1),
                    string.say(#2)
                )
            ]"""
        )
        path.fast_forward()
        path = os.path.join("parquet", "person.parquet")
        # Open the Parquet file
        p = pq.ParquetFile(path)

        # Read specific columns
        table = p.read(columns=["firstname", "lastname"])
        assert table
        print(f"table = {table}")
        chunked_array = table.column("firstname")
        for chunk in chunked_array.chunks:
            for value in chunk:
                print(f"value: {value}")
        assert str(chunked_array[2]) == "Fish"

    ###########

    # decimal,integer,boolean,date,datetime,none,email,url,string

    def test_function_parquet_3(self):
        nos = Nos("parquet")
        if nos.dir_exists():
            nos.remove()
            nos.makedirs()
        path = os.path.join("parquet", "types.parquet")
        nos = Nos(path)
        assert not nos.exists()

        csvpath = CsvPath()
        csvpath.parse(
            f"""
            ~ validation-mode:raise~
            ${TYPES}[1]
            [
                parquet.types(
                    decimal.price(#0),
                    integer.quantity(#1),
                    boolean.truth(#2),
                    date(#when),
                    datetime.point_in_time(#"exactly when"),
                    none.nothing(#Nothing),
                    string(#an_email),
                    string.url(#7),
                    string.a_string(#a_string)
                )
            ]"""
        )
        lines = csvpath.collect()
        print(f"lines: {lines}")
        assert lines
        assert len(lines) == 1
        assert csvpath.has_errors() is False
        errors = csvpath.errors
        assert len(errors) == 0

        """
        p = pq.ParquetFile(path)
        table = p.read(columns=['truth', 'date'])
        print(f"table = {table}")
        assert table

        chunked_array = table.column("truth")
        for chunk in chunked_array.chunks:
            for value in chunk:
                print(f"value: {value}")

        assert str(chunked_array[2]) == "false"
        """

    def test_function_parquet_util_string_1(self):
        s = fact.get_function(
            None, name="string", child=None, find_external_functions=False
        )
        assert s is not None
        t = paut.to_type(s)
        print(f"s: {s}, t: {t}: {type(t[0])}")
        assert isinstance(t, list)
        t = t[0]
        assert isinstance(t, DataType)
        assert t == pa.string()

    def test_function_parquet_util_integer_1(self):
        s = fact.get_function(
            None, name="integer", child=None, find_external_functions=False
        )
        assert s is not None
        t = paut.to_type(s)
        print(f"s: {s}, t: {t}: {type(t[0])}")
        assert isinstance(t, list)
        t = t[0]
        assert isinstance(t, DataType)
        assert pa.types.is_integer(t)

    def test_function_parquet_util_decimal_1(self):
        s = fact.get_function(
            None, name="decimal", child=None, find_external_functions=False
        )
        assert s is not None
        t = paut.to_type(s)
        print(f"s: {s}, t: {t}: {type(t[0])}")
        assert isinstance(t, list)
        t = t[0]
        assert isinstance(t, DataType)
        assert pa.types.is_floating(t)

    def test_function_parquet_util_boolean_1(self):
        s = fact.get_function(
            None, name="boolean", child=None, find_external_functions=False
        )
        assert s is not None
        t = paut.to_type(s)
        print(f"s: {s}, t: {t}: {type(t[0])}")
        assert isinstance(t, list)
        t = t[0]
        assert isinstance(t, DataType)
        assert t == pa.bool_()

    def test_function_parquet_util_date_1(self):
        s = fact.get_function(
            None, name="date", child=None, find_external_functions=False
        )
        assert s is not None
        t = paut.to_type(s)
        print(f"s: {s}, t: {t}: {type(t[0])}")
        assert isinstance(t, list)
        t = t[0]
        assert isinstance(t, DataType)
        assert pa.types.is_date(t)

    def test_function_parquet_util_datetime_1(self):
        s = fact.get_function(
            None, name="datetime", child=None, find_external_functions=False
        )
        assert s is not None
        t = paut.to_type(s)
        print(f"s: {s}, t: {t}: {type(t[0])}")
        assert isinstance(t, list)
        t = t[0]
        assert isinstance(t, DataType)
        assert pa.types.is_timestamp(t)

    def test_function_parquet_util_none_1(self):
        s = fact.get_function(
            None, name="none", child=None, find_external_functions=False
        )
        assert s is not None
        t = paut.to_type(s)
        print(f"s: {s}, t: {t}: {type(t[0])}")
        assert isinstance(t, list)
        t = t[0]
        assert isinstance(t, DataType)
        assert t == pa.null()

    # url, email, blank, wildcard

    def test_function_parquet_util_email_1(self):
        s = fact.get_function(
            None, name="email", child=None, find_external_functions=False
        )
        assert s is not None
        t = paut.to_type(s)
        print(f"s: {s}, t: {t}: {type(t[0])}")
        assert isinstance(t, list)
        t = t[0]
        assert isinstance(t, DataType)
        assert t == pa.string()

    def test_function_parquet_util_url_1(self):
        s = fact.get_function(
            None, name="url", child=None, find_external_functions=False
        )
        assert s is not None
        t = paut.to_type(s)
        print(f"s: {s}, t: {t}: {type(t[0])}")
        assert isinstance(t, list)
        t = t[0]
        assert isinstance(t, DataType)
        assert t == pa.string()

    def test_function_parquet_util_blank_1(self):
        s = fact.get_function(
            None, name="blank", child=None, find_external_functions=False
        )
        assert s is not None
        t = paut.to_type(s)
        print(f"s: {s}, t: {t}: {type(t[0])}")
        assert isinstance(t, list)
        t = t[0]
        assert isinstance(t, DataType)
        assert t == pa.string()

    def test_function_parquet_util_wildcard_1(self):
        s = fact.get_function(
            None, name="wildcard", child=None, find_external_functions=False
        )
        i = Term(None, value=1)
        s.add_child(i)
        assert s is not None
        t = paut.to_type(s)
        print(f"test_function_parquet_util_wildcard_1: s: {s}, t: {t}")
        assert isinstance(t, list)
        assert len(t) == 0

    def test_function_parquet_util_wildcard_2(self):
        s = fact.get_function(
            None, name="wildcard", child=None, find_external_functions=False
        )
        i = Term(None, value=5)
        s.add_child(i)
        assert s is not None
        t = paut.to_type(s)
        print(f"test_function_parquet_util_wildcard_2: s: {s}, t: {t}")
        assert isinstance(t, list)
        assert len(t) == 0

    def test_function_parquet_util_wildcard_3(self):
        s = fact.get_function(
            None, name="wildcard", child=None, find_external_functions=False
        )
        i = Term(None, value="*")
        s.add_child(i)
        assert s is not None
        t = paut.to_type(s)
        print(f"test_function_parquet_util_wildcard_3: s: {s}, t: {t}")
        assert isinstance(t, list)
        assert len(t) == 0

    def test_function_parquet_columns_1(self):
        line = fact.get_function(
            None, name="line", child=None, find_external_functions=False
        )
        eq = Equality(None)
        line.add_child(eq)
        string = fact.get_function(
            None, name="string.firstname", child=None, find_external_functions=False
        )
        integer = fact.get_function(
            None, name="integer.zipcode", child=None, find_external_functions=False
        )
        eq.add_child(string)
        eq.add_child(integer)
        cs = paut.columns(line)
        assert cs
        assert len(cs) == 2
        assert cs[0][1] == pa.string()
        assert pa.types.is_integer(cs[1][1])
