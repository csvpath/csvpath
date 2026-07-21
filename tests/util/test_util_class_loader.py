import os
import unittest
import pytest
from csvpath.util.class_loader import ClassLoader, ClassLoadingError
from csvpath.util.stopwatch import Stopwatch
from csvpath.util.config import Config

BASE_PATH = os.path.join("tests", "util", "test_resources", "class_loader", "one")


class TestUtilClassLoader(unittest.TestCase):
    #
    # load()
    #
    def test_load_instantiates_with_args_and_kwargs(self):
        instance = ClassLoader.load(
            "from csvpath.util.stopwatch import Stopwatch",
            args=[100],
            kwargs={"mark": "hi"},
        )
        assert isinstance(instance, Stopwatch)
        assert instance.slow == 100

    def test_load_defaults_args_and_kwargs_to_empty(self):
        instance = ClassLoader.load("from csvpath.util.stopwatch import Stopwatch")
        assert isinstance(instance, Stopwatch)
        assert instance.slow == 150

    def test_load_empty_string_returns_none(self):
        assert ClassLoader.load("") is None

    def test_load_whitespace_only_returns_none(self):
        assert ClassLoader.load("   ") is None

    def test_load_malformed_statement_raises(self):
        with pytest.raises(ClassLoadingError):
            ClassLoader.load("import csvpath.util.stopwatch.Stopwatch")

    def test_load_too_few_tokens_raises(self):
        with pytest.raises(ClassLoadingError):
            ClassLoader.load("from csvpath.util.stopwatch")

    #
    # load_private_class()
    #
    def test_load_private_class_instantiates(self):
        instance = ClassLoader.load_private_class(
            BASE_PATH, "from greeter import Greeter", "Ann"
        )
        assert instance.greet() == "Hello, Ann!"

    def test_load_private_class_with_kwargs(self):
        instance = ClassLoader.load_private_class(
            BASE_PATH, "from greeter import Greeter", "Ann", greeting="Hi"
        )
        assert instance.greet() == "Hi, Ann!"

    def test_load_private_class_none_statement_raises(self):
        with pytest.raises(ValueError):
            ClassLoader.load_private_class(BASE_PATH, None)

    def test_load_private_class_empty_statement_raises(self):
        with pytest.raises(ValueError):
            ClassLoader.load_private_class(BASE_PATH, "   ")

    def test_load_private_class_malformed_statement_raises(self):
        with pytest.raises(ClassLoadingError):
            ClassLoader.load_private_class(BASE_PATH, "import greeter.Greeter")

    def test_load_private_class_missing_module_raises(self):
        with pytest.raises(ImportError):
            ClassLoader.load_private_class(BASE_PATH, "from nosuchmodule import Nope")

    #
    # load_private_function()
    #
    def test_load_private_function_instantiates(self):
        config = Config()
        config.set(
            section="functions",
            name="imports",
            value=os.path.join(BASE_PATH, "greeter.imports"),
        )
        instance = ClassLoader.load_private_function(
            config, "from greeter import Greeter", "Ann"
        )
        assert instance.greet() == "Hello, Ann!"

    def test_load_private_function_missing_imports_raises(self):
        config = Config()
        config.set(section="functions", name="imports", value=None)
        with pytest.raises(ValueError):
            ClassLoader.load_private_function(config, "from greeter import Greeter")

    def test_load_private_function_empty_imports_raises(self):
        config = Config()
        config.set(section="functions", name="imports", value="   ")
        with pytest.raises(ValueError):
            ClassLoader.load_private_function(config, "from greeter import Greeter")
