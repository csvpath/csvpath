import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"


class TestFunctionsContains(unittest.TestCase):
    def test_function_contains_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @s = "fresh fish"
                @s2 = "fish"
                @c = contains(@s, @s2)
            ]"""
        ).collect()
        assert path.variables["c"] is True

    def test_function_contains_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @s = "fresh fish"
                @s2 = "whale"
                @c = contains(@s, @s2)
            ]"""
        ).collect()
        assert path.variables["c"] is False

    def test_function_contains_3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @s = none()
                @s2 = "whale"
                @c = contains(@s, @s2)
            ]"""
        ).collect()
        assert path.variables["c"] is False

    def test_function_contains_4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @s = "seafish"
                @s2 = none()
                @c = contains(@s, @s2)
            ]"""
        ).collect()
        assert path.variables["c"] is False

    def test_function_contains_5(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @s = none()
                @s2 = none()
                @c = contains(@s, @s2)
            ]"""
        ).collect()
        assert path.variables["c"] is False

    def test_function_find_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @s = "fresh fish"
                @s2 = "fish"
                @c = find(@s, @s2)
            ]"""
        ).collect()
        assert path.variables["c"] == 6

    def test_function_find_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @s = "fresh fish"
                @s2 = "turtle"
                @c = find(@s, @s2)
            ]"""
        ).collect()
        assert path.variables["c"] == -1

    def test_function_find_3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @s = none()
                @s2 = "turtle"
                @c = find(@s, @s2)
            ]"""
        ).collect()
        assert path.variables["c"] == -1

    def test_function_find_4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @s = "seafish"
                @s2 = none()
                @c = find(@s, @s2)
            ]"""
        ).collect()
        assert path.variables["c"] == -1

    def test_function_find_5(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @s = none()
                @s2 = none()
                @c = find(@s, @s2)
            ]"""
        ).collect()
        assert path.variables["c"] == -1
