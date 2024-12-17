# pylint: disable=C0114
import os
import importlib
from csvpath.util.config_exception import ConfigurationException
from .boolean.yes import Yes


class FunctionFinder:  # pylint: disable=R0903
    #
    # re: R0903 -- too few public methods: moved here from FunctionFactory
    # to keep that class from becoming even larger. at some point this should
    # merge with csvpath.util.ClassLoader in some way.
    #
    EXTERNALS = "externalfunctionsloaded"

    @classmethod
    def load(cls, matcher, func_fact) -> None:
        # any problems loading will bubble up to the nearest
        # expression and be handled there.
        config = matcher.csvpath.config
        # find the list
        path = config.function_imports
        # read the list
        if path is None:
            matcher.csvpath.logger.error("No [functions][imports] in config.ini")
            return
        if not os.path.exists(path):
            matcher.csvpath.logger.error(
                f"[functions][imports] path in {config.configpath} does not exist"
            )
            return
        with open(path, "r", encoding="utf-8") as file:
            i = 0
            for line in file:
                i += 1
                cls._add_function(matcher, func_fact, line)
            matcher.csvpath.logger.info("Added %s external functions", i)
        # add a sentinel to keep us from attempting reload.
        # this instance will never be found, but the dict will
        # never be empty
        func_fact.add_function(cls.EXTERNALS, Yes(None, cls.EXTERNALS))

    @classmethod
    def _add_function(cls, matcher, func_fact, s: str) -> None:
        s = s.strip()
        if s != "":
            instance = None
            # instantiate the classes
            # function_name module classname
            cs = s.split(" ")
            #
            # lines in config are like:
            #   from module import class as function-name
            #
            if len(cs) == 6 and cs[0] == "from" and cs[2] == "import" and cs[4] == "as":
                module = importlib.import_module(cs[1])
                class_ = getattr(module, cs[3])
                instance = class_(matcher, cs[5])
                # load to FunctionFactory.add
                func_fact.add_function(cs[5], instance)
            else:
                raise ConfigurationException(
                    "Unclear external function import setup: {s}"
                )
