from csvpath.util.references.reference_parser import ReferenceParser


class TemplateUtility:
    @classmethod
    def get_template_suffix(
        cls, *, template: str = None, ref: str = None, csvpaths=None
    ) -> str:
        #
        # this is pretty flexible. in general we'd expect to pass the template in.
        #
        if template is None and (ref is None or csvpaths is None):
            raise ValueError(
                "You must pass a template or, alternatively, both a reference and a CsvPaths instance"
            )
        if template is None:
            template = cls.find_template(csvpaths, ref)
        if template is None:
            raise ValueError("Cannot find template for reference: {ref}")
        cls.valid(template)
        i = template.find(":run_dir")
        s = template[i + 8 :]
        return s

    # csvpaths: "CsvPaths" disallowed by flake
    @classmethod
    def strip_suffix(cls, csvpaths, template: str) -> str:
        #
        # remove dead code?
        #
        if template is not None:
            suffix = cls.get_template_suffix(csvpaths=csvpaths, template=template)
            template = template[0 : len(template) - len(suffix)]
            return template
        return None

    @classmethod
    def find_template(cls, csvpaths, ref: str) -> str:
        ref = ReferenceParser(ref, csvpaths=self.csvpaths)
        paths = ref.root_major
        #
        # TODO: a reference could be FILES not just CSVPATHS.
        #
        t = csvpaths.paths_manager.get_template_for_paths(paths)
        return t

    @classmethod
    def valid(cls, template: str, file: bool = False) -> None:
        v, r = cls.validate(template, file=file)
        if not v:
            raise ValueError(r)

    @classmethod
    def validate(cls, template: str, file: bool = False) -> tuple[bool, str]:
        #
        # removed the windows \\ rules because we cannot assume a dev using windows
        # works in a purely windows env. may need to convert seps in some step.
        #
        #
        # cannot be empty
        #
        if template is None:
            return (True, "No template")
        if template is None or template.strip() == "":
            return (False, "Templates cannot be the empty string")
        #
        # must end in '/:run_dir'. this is a change from the orig which just required
        # a run_dir. now we require it to be the end of the template.
        #
        e = ":filename" if file else ":run_dir"
        if not template.endswith(e):
            return (False, f"Must end in {e}")
        #
        # if r == -1:
        #    return False
        #
        # cannot start or end with path separators
        #
        if template.startswith("/"):
            return (False, "Cannot start with a slash")
        #
        # must have path separators before :run_dir
        #
        r = template.find(e)
        if r == 0:
            return (False, f"Cannot start with {e}")
        if template[r - 1] != "/":
            return (False, f"{e} must follow a path separator")
        #
        #
        #
        if template.find("\\") > -1:
            return (False, "Templates use forward-slash path separators")
        #
        # remove run_dir or filename for remaining tests
        #
        t2 = template.rstrip(f"/{e}")
        #
        # cannot be just ":run_dir". covered this above, no?
        #
        if t2 == "/" or t2.strip() == "":
            return (False, "Cannot be solely {e}")
        #
        # index pointers must be the only other uses of colon and
        # must have 1 or 2 integers, not 3
        #
        for i, c in enumerate(t2):
            #
            # proper use of ':'
            #
            if c == ":":
                if i == len(t2) - 1:
                    return False
                ns = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
                if t2[i + 1] not in ns:
                    return (False, "Colon-led tokens must be numbers or :run_dir")
                try:
                    if t2[i + 2] in ns and t2[i + 3] in ns:
                        return False
                except Exception:
                    ...
            #
            # no illegal chars
            #
            elif c in ["[", "]", "?", "!", "{", "}", "#", "`", ".", "(", ")"]:
                return (False, "Illegal character")
            #
            # cannot begin or end in '/' or have double slashes
            #
            elif c == "/":
                if t2[i + 1] == "/":
                    return (False, "Cannot have leading or double-slashes")
        return (True, "Good template")
