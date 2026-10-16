from ...reference_3 import Reference3
from ..function_3 import Function3


class FileName3(Function3):
    #
    # Named-File Manifest (table 1) and Named-File Arrivals Manifest
    # (table 2, global) -- added 2026-10-15, closing the deferred-work
    # bucket list gap of the same name. Confirmed against the real write
    # path before building, not guessed: `FileRegistrar.metadata_
    # update()` writes `mani["file_name"] = mdata.file_name` onto table
    # 1, and `FilesListener`'s own global-ledger write does the
    # identical thing onto table 2 -- both already populated by
    # `FileManager`'s own `mdata.file_name = file_home[file_home.rfind(
    # nos.sep) + 1 :]` (the basename of `file_home`), confirming the
    # doc's own description ("the same name as the file home
    # directory") is accurate and this is a real, already-written field
    # on both tables, not something needing a `SOURCE = "computed"`
    # derivation the way `:named_file_home()` needed. Distinct from
    # `:file_home()` (the directory *path*) and `:named_file_name()`
    # (the resolved named-file's own registered NAME, a different
    # concept -- "acme", not "orders.csv").
    #
    NAME = "file_name"
    SUMMARY = (
        "The simple (base) name of the original physical file that was "
        "registered -- the same name as the file home directory."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "file_name",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_THREE,)}
