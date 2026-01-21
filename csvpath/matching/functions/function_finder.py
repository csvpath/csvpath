# pylint: disable=C0114
import os
import importlib
from csvpath.util.config_exception import ConfigurationException
from csvpath.util.class_loader import ClassLoader
from .boolean.yes import Yes


class FunctionFinder:  # pylint: disable=R0903
    #
    # if we don't have a matcher.csvpath.config to get a [functions] imports path
    # from we use this token as the no-reload sentinel. in the usual case we will
    # be able to get the actual path.
    #
    EXTERNALS = "externalfunctionsloaded"

    @classmethod
    def load(cls, matcher, func_fact) -> None:
        # any problems loading will bubble up to the nearest
        # expression and be handled there.
        print("fun fndrx: loading")
        if matcher and matcher.csvpath and matcher.csvpath.config:
            config = matcher.csvpath.config
            path = config.function_imports
            if path is None or path.strip() == "":
                matcher.csvpath.logger.error("No [functions][imports] in config.ini")
                return
            cls._debug_one(matcher, "Functions import file is at %s", path)
            if not os.path.exists(path):
                matcher.csvpath.logger.error(
                    f"[functions][imports] path {path} in {config.configpath} does not exist"
                )
                raise ValueError(
                    f"[functions][imports] path {path} in {config.configpath} does not exist"
                )
            with open(path, "r", encoding="utf-8") as file:
                i = 0
                for line in file:
                    i += 1
                    line = str(line).strip()
                    if line == "" or line.startswith("#"):
                        continue
                    cls._debug_one(matcher, "Adding function %s", line)
                    try:
                        cls._add_function(matcher, func_fact, line)
                    except Exception:
                        matcher.csvpath.logger.exception(
                            f"Could not add function for '{line}'"
                        )
                matcher.csvpath.logger.info("Added %s external functions", i)
        # add a sentinel to keep us from attempting reload.
        # this instance will never be found, but the dict will
        # never be empty
        e = cls.externals_sentinel(matcher)
        func_fact.add_function(e, Yes(None, e))
        cls._debug_one(matcher, "Added sentinel function %s", e)

    @classmethod
    def _debug_one(cls, matcher, txt: str, obj=None) -> None:
        if matcher is None:
            return
        if matcher.csvpath is None:
            return
        matcher.csvpath.logger.debug(txt, str(obj))

    @classmethod
    def _debug_two(cls, matcher, txt: str, obj=None, obj2=None) -> None:
        if matcher is None:
            return
        if matcher.csvpath is None:
            return
        matcher.csvpath.logger.debug(txt, str(obj), str(obj2))

    @classmethod
    def externals_sentinel(cls, matcher) -> str:
        if matcher and matcher.csvpath:
            #
            # sentinel is based on the function file path so that when we find a new path
            # we load its functions. if we need to load the same path multiple times we
            # need to use clear_to_reload
            #
            config = matcher.csvpath.config
            _ = config.get(section="functions", name="imports", default=cls.EXTERNALS)
            e = cls.externals_sentinel_from_path(_)
            return e
        else:
            return cls.EXTERNALS

    @classmethod
    def externals_sentinel_from_path(cls, path: str) -> str:
        e = f"sentinel{hash(path)}"
        e = e.replace("-", "_")
        return e

    @classmethod
    def _add_function(cls, matcher, func_fact, s: str) -> None:
        s = s.strip()
        if s is None or s == "":
            raise ValueError("External function import statement cannot be None or ''")
        instance = None
        # instantiate the classes
        # function_name module classname
        cs = s.split(" ")
        #
        # lines in config are like:
        #   from module import class as function-name
        #
        cls._debug_one(matcher, "Import line is %s", cs)
        if len(cs) == 6 and cs[0] == "from" and cs[2] == "import" and cs[4] == "as":
            config = matcher.csvpath.config
            try:
                instance = ClassLoader.load_private_function(config, s, matcher, cs[5])
                qname = func_fact.qname(matcher=matcher, name=cs[5])
                cls._debug_two(
                    matcher, "Adding custom function %s: %s", qname, instance
                )
                func_fact.add_function(qname, instance)
            except Exception:
                if matcher is not None and matcher.csvpath is not None:
                    matcher.csvpath.logger.exception(f"Cannot load class {cs}")
                #
                # matcher and csvpath will be present, but we check to be sure. there's no
                # fallback because it is an unlikely scenario that would have its own logic.
                #
        else:
            raise ConfigurationException("Unclear external function imports: {s}")
