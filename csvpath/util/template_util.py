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

    @classmethod
    def find_template(self, csvpaths, ref: str) -> str:
        ref = ReferenceParser(ref)
        paths = ref.root_major
        #
        # TODO: a reference could be FILES not just CSVPATHS.
        #
        t = csvpaths.paths_manager.get_template_for_paths(paths)
        return t

    @classmethod
    def valid(self, template: str) -> bool:
        #
        # removed the windows \\ rules because we cannot assume a dev using windows
        # works in a purely windows env. may need to convert seps in some step.
        #
        #
        # cannot be empty
        #
        if template is None or template.strip() == "":
            return False
        #
        # must have '/:run_dir/'
        #
        t = len(template)
        r = template.find(":run_dir")
        if r == -1:
            return False
        #
        # cannot start or end with path separators
        #
        if template.startswith("/") or template.endswith("/"):
            return False
        #
        # must have path separators around :run_dir or beginning or end of template
        #
        if r != 0 and template[r - 1] != "/":
            return False
        if r + 9 <= t and template[r + 8] != "/":
            return False
        #
        # cannot use both '/' and '\\'
        #
        # if template.find("/") > -1 and template.find("\\") > -1:
        if template.find("\\") > -1:
            return False
        #
        # remove run_dir for remaining tests
        #
        t2 = None
        t2 = template.replace("/:run_dir/", "/")
        t2 = t2.rstrip("/:run_dir")
        #
        # cannot be just ":run_dir"
        #
        if t2 == "/" or t2.strip() == "":
            return False
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
                    return False
                try:
                    if t2[i + 2] in ns and t2[i + 3] in ns:
                        return False
                except Exception:
                    ...
            #
            # no illegal chars
            #
            elif c in ["[", "]", "?", "!", "{", "}", "#", "`", ".", "(", ")"]:
                return False
            #
            # cannot begin or end in '/' or have double slashes
            #
            elif c == "/":
                if t2[i + 1] == "/":
                    return False
        return True
