import importlib
import os
from typing import Any


class ClassLoadingError(RuntimeError):
    ...


class ClassLoader:
    #
    # load is fine for classes we expect. e.g. we load specific types of data readers and writers
    # using this method without any concerns about different projects needing to not collide. today
    # we treat integration listeners the same way, but longer term we need those to be able to be
    # custom loaded too.
    #
    @classmethod
    def load(cls, s: str, args: list = None, kwargs: dict = None) -> Any:
        s = s.strip()
        if s != "":
            instance = None
            cs = s.split(" ")
            #
            # lines in config are like:
            #   from module import class
            #
            if len(cs) == 4 and cs[0] == "from" and cs[2] == "import":
                module = importlib.import_module(cs[1])
                class_ = getattr(module, cs[3])
                args = args if args is not None else []
                kwargs = kwargs if kwargs is not None else {}
                instance = class_(*args, **kwargs)
                return instance
            else:
                raise ClassLoadingError(f"Unclear class loading import statement: {s}")
        return None

    #
    # this loads a custom function using a name that is distinct across projects so there
    # is no risk of name collisions.
    #
    @classmethod
    def load_private_function(cls, config, stmt: str, *args, **kwargs):
        imports = config.get(section="functions", name="imports")
        if not imports or str(imports).strip() == "":
            raise ValueError("Imports cannot be None or ''")
        imports = os.path.dirname(imports)
        return cls.load_private_class(imports, stmt, *args, **kwargs)

    @classmethod
    def load_private_class(cls, base_path: str, stmt: str, *args, **kwargs):
        if not stmt or stmt.strip() == "":
            raise ValueError("Load statement cannot be None or ''")
        module_name = None
        class_name = None
        #
        # remove the imports file name. functions must be in or below the dir
        # where the functions file is.
        #
        # /x/y/z/function.imports
        # /x/y/z
        # from a.b.c import C as cone
        #
        # we look in /x/y/z/a/b/c.py for class C
        #             base  module             clss
        #
        cs = stmt.split(" ")
        if len(cs) >= 4 and cs[0] == "from" and cs[2] == "import":
            module_name = cs[1]
            class_name = cs[3]
        else:
            raise ClassLoadingError(f"Unclear class loading import statement: {stmt}")
        #
        # Resolve the file path for the module
        #
        module_path = os.path.join(base_path, module_name)
        module_path = module_path.replace(".", os.sep)
        module_path = f"{module_path}.py"
        if not os.path.exists(module_path):
            raise ImportError(f"Module not found in {module_path}")
        #
        # create a unique module spec. we hash the full path to the bytes in order
        # to make sure we have a distinct class, even if one project names and locates
        # a class in the exact same relative location.
        #
        # e.g. project A has a function.imports file at config/function.imports that defines a class B as:
        #           from b import B as bee
        #      project B has a function.imports file at config/function.imports that defines a class B as:
        #           from b import B as bee
        #      These two class Bs would be identified exactly the same way even though they are different. We
        #      don't ever want a request for project B's class B to be returned when project A requests a
        #      class B. The hash keeps the names distinct.
        #
        spec = importlib.util.spec_from_file_location(
            f"{module_name}_{hash(module_path)}",  # unique name per loader instance
            str(module_path),
        )
        module = importlib.util.module_from_spec(spec)
        loader = spec.loader
        if loader is None:
            raise ImportError(f"Could not load spec for {module_name} at {module_path}")
        loader.exec_module(module)
        cls = getattr(module, class_name)
        instance = cls(*args, **kwargs)
        return instance
