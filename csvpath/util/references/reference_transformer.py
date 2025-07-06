from lark import Lark, Transformer, v_args, Tree, Token


class ReferenceTransformer(Transformer):
    def __init__(self, ref) -> None:
        self.ref = ref
        self.seq = self.ref.sequence

    def root_name(self, items):
        self.seq.append("root_name")
        name = None
        if items and len(items) > 0 and items[0]:
            name = items[0].value
            name = str(name)
            self.ref.root_name = name
        return name

    def root_minor_name(self, items):
        name = items[0].value
        self.ref.root_minor = name

    # =====================
    # results
    # =====================

    def files_arrival(self, items):
        self.ref.name_one = items[0]
        self.seq.append("files_arrival")
        self.ref.next = ["files_arrival_ordinal", "files_arrival_range"]

    def files_arrival_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_arrival_ordinal")
        self.ref.next = []

    def files_arrival_range(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_arrival_range")
        self.ref.next = ["files_arrival_range_ordinal"]

    def files_arrival_range_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_arrival_range_ordinal")
        self.ref.next = []

    def files_arrival_two_arrival(self, items):
        self.ref.name_three = items[0]
        self.seq.append("files_arrival_two_arrival")
        self.ref.next = ["files_arrival_two_arrival_range"]

    def files_arrival_two_arrival_range(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("files_arrival_two_arrival_range")
        self.ref.next = ["files_arrival_two_arrival_range_ordinal"]

    def files_arrival_two_arrival_range_ordinal(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("files_arrival_two_arrival_range_ordinal")
        self.ref.next = []

    def files_path(self, items):
        self.ref.name_one = items[0]
        self.seq.append("files_path")
        self.ref.next = ["files_path_arrival", "files_path_ordinal", "files_path_range"]

    def files_path_arrival(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_path_arrival")
        self.ref.next = ["files_path_arrival_ordinal", "files_path_arrival_range"]

    def files_path_arrival_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_path_arrival_ordinal")
        self.ref.next = []

    def files_path_arrival_range(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_path_arrival_range")
        self.ref.next = ["files_path_arrival_range_ordinal"]

    def files_path_arrival_range_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_path_arrival_range_ordinal")
        self.ref.next = []

    def files_path_two_arrival(self, items):
        self.ref.name_three = items[0]
        self.seq.append("files_path_two_arrival")
        self.ref.next = [
            "files_path_two_arrival_range",
            "files_path_two_arrival_ordinal",
        ]

    def files_path_two_arrival_range(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("files_path_two_arrival_range")
        self.ref.next = ["files_path_two_arrival_range_ordinal"]

    def files_path_two_arrival_range_ordinal(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("files_path_two_arrival_range_ordinal")
        self.ref.next = []

    def files_path_two_arrival_ordinal(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("files_path_two_arrival_ordinal")
        self.ref.next = []

    def files_path_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_path_ordinal")
        self.ref.next = []

    def files_path_range(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_path_range")
        self.ref.next = ["files_path_range_arrival"]

    def files_path_range_arrival(self, items):
        self.ref.name_three = items[0]
        self.seq.append("files_path_range_arrival")
        self.ref.next = ["files_path_range_arrival_range"]

    def files_path_range_arrival_range(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("files_path_range_arrival_range")
        self.ref.next = ["files_path_range_arrival_range_ordinal"]

    def files_path_range_arrival_range_ordinal(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("files_path_range_arrival_range_ordinal")
        self.ref.next = []

    def files_path_range_arrival_ordinal(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("files_path_range_arrival_ordinal")
        self.ref.next = []

    def files_path_range_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_path_range_ordinal")
        self.ref.next = []

    def files_range(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_range")
        self.ref.next = ["files_range_ordinal"]

    def files_range_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_range_ordinal")
        self.ref.next = []

    def files_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("files_ordinal")
        self.ref.next = []

    # =====================
    # results
    # =====================

    def results_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("results_ordinal")
        self.ref.next = []

    def results_range(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("results_range")
        self.ref.next = []

    def results_range_ordinal_instance(self, items):
        self.ref.name_three = items[0]
        self.seq.append("results_range_ordinal_instance")
        self.ref.next = []

    def results_range_ordinal_instance_data(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("results_range_ordinal_instance_data")
        self.ref.next = []

    def results_range_ordinal_instance_unmatched(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("results_range_ordinal_instance_unmatched")
        self.ref.next = []

    def results_range_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("results_range_ordinal")
        self.ref.next = []

    def results_ordinal_instance(self, items):
        self.ref.name_three = items[0]
        self.seq.append("results_ordinal_instance")
        self.ref.next = []

    def results_ordinal_instance_data(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("results_ordinal_instance_data")
        self.ref.next = []

    def results_ordinal_instance_unmatched(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("results_ordinal_instance_unmatched")
        self.ref.next = []

    def run_date(self, items):
        self.ref.name_one = items[0]
        self.seq.append("run_date")
        self.ref.next = []

    def run_date_instance(self, items):
        self.ref.name_three = items[0]
        self.seq.append("run_date_instance")
        self.ref.next = []

    def run_date_instance_data(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_date_instance_data")
        self.ref.next = []

    def run_date_instance_unmatched(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_date_instance_unmatched")
        self.ref.next = []

    def ordinal(self, items):
        self.seq.append("ordinal")
        self.ref.next = []
        return items[0]

    def range(self, items):
        self.seq.append("range")
        self.ref.next = []
        return items[0]

    def no_timebox_range(self, items):
        self.seq.append("no_timebox_range")
        self.ref.next = []
        return items[0]

    def run_date_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("run_date_ordinal")
        self.ref.next = []

    def run_date_ordinal_instance(self, items):
        self.ref.name_three = items[0]
        self.seq.append("run_date_ordinal_instance")
        self.ref.next = []

    def run_date_ordinal_instance_data(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_date_ordinal_instance_data")
        self.ref.next = []

    def run_date_ordinal_instance_unmatched(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_date_ordinal_instance_unmatched")
        self.ref.next = []

    def run_date_range(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("run_date_range")
        self.ref.next = []

    def run_date_range_date(self, items):
        self.ref.name_three = items[0]
        self.seq.append("run_date_range_date")
        self.ref.next = []

    def run_date_range_date_range(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_date_range_date_range")
        self.ref.next = []

    def run_date_range_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("run_date_range_ordinal")
        self.ref.next = []

    def run_date_range_ordinal_instance(self, items):
        self.ref.name_three = items[0]
        self.seq.append("run_date_range_ordinal_instance")
        self.ref.next = []

    def run_date_range_ordinal_instance_data(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_date_range_ordinal_instance_data")
        self.ref.next = []

    def run_date_range_ordinal_instance_unmatched(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_date_range_ordinal_instance_unmatched")
        self.ref.next = []

    def run_path(self, items):
        self.ref.name_one = items[0]
        self.seq.append("run_path")
        self.ref.next = []

    def run_path_date(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("run_path_date")
        self.ref.next = []

    def run_path_date_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("run_path_date_ordinal")
        self.ref.next = []

    def run_path_date_range(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("run_path_date_range")
        self.ref.next = []

    def run_path_date_range_date(self, items):
        self.ref.name_three = items[0]
        self.seq.append("run_path_date_range_date")
        self.ref.next = []

    def run_path_date_ordinal_instance(self, items):
        self.ref.name_three = items[0]
        self.seq.append("run_path_date_ordinal_instance")
        self.ref.next = []

    def run_path_date_ordinal_instance_data(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_path_date_ordinal_instance_data")
        self.ref.next = []

    def run_path_date_ordinal_instance_unmatched(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_path_date_ordinal_instance_unmatched")
        self.ref.next = []

    def run_path_date_range_date_range(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_path_date_range_date_range")
        self.ref.next = []

    def run_path_range(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("run_path_range")
        self.ref.next = []

    def run_path_range_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("run_path_range_ordinal")
        self.ref.next = []

    def run_path_range_ordinal_instance(self, items):
        self.ref.name_three = items[0]
        self.seq.append("run_path_range_ordinal_instance")
        self.ref.next = []

    def run_path_range_ordinal_instance_data(self, items):
        self.ref.append_name_three_token("data")
        self.seq.append("run_path_range_ordinal_instance_data")
        self.ref.next = []

    def run_path_range_ordinal_instance_unmatched(self, items):
        self.ref.append_name_three_token("unmatched")
        self.seq.append("run_path_range_ordinal_instance_unmatched")
        self.ref.next = []

    def run_path_ordinal(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("run_path_ordinal")
        self.ref.next = []

    def run_path_ordinal_instance(self, items):
        self.ref.name_three = items[0]
        self.seq.append("run_path_ordinal_instance")
        self.ref.next = []

    def run_path_ordinal_instance_data(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_path_ordinal_instance_data")
        self.ref.next = []

    def run_path_ordinal_instance_unmatched(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_path_ordinal_instance_unmatched")
        self.ref.next = []

    def run_path_instance(self, items):
        self.ref.name_three = items[0]
        self.seq.append("run_path_instance")
        self.ref.next = []

    def run_path_instance_data(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_path_instance_data")
        self.ref.next = []

    def run_path_instance_unmatched(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("run_path_instance_unmatched")
        self.ref.next = []

    def csvpaths_instance_name_one_range(self, items):
        self.ref.append_name_one_token(items[0])
        self.seq.append("csvpaths_instance_name_one_range")
        self.ref.next = []

    def csvpaths_instance_name_three_range(self, items):
        self.ref.append_name_three_token(items[0])
        self.seq.append("csvpaths_instance_name_three_range")
        self.ref.next = []

    def csvpaths_instance_name_one(self, items):
        #: IDENTIFIER | /\d{1,3}/ | ":" /\d{1,3}/
        self.ref.name_one = items[0].value
        self.seq.append("csvpaths_instance_name_one")
        self.ref.next = []

    def csvpaths_instance_name_three(self, items):
        #: IDENTIFIER | /\d{1,3}/ | ":" /\d{1,3}/
        self.ref.name_three = items[0]
        self.seq.append("csvpaths_instance_name_three")
        self.ref.next = []

    def reference_major_name(self, items):
        # IDENTIFIER
        self.ref.name_one = items[0]
        self.seq.append("reference_major_name")
        self.ref.next = []

    def reference_minor_name(self, items):
        # IDENTIFIER
        self.ref.name_three = items[0]
        self.seq.append("reference_minor_name")
        self.ref.next = []

    # ==============================================================
    # ==============================================================
    # ==============================================================

    #
    # name two becomes name three after we're done parsing because
    # names one and two (in the query parser) are both potentially
    # split in two around a '#' to make names one through four. the
    # rest of CsvPath uses ReferenceParser as the reference class
    # and so knows name_one, name_two, name_three, and name_four,
    # with focus being on names one and three.
    #

    def local_name_one(self, items):
        if items[0] is not None:
            self.ref.name_one = items[0].value

    def local_name_two(self, items):
        if items[0] is not None:
            self.ref.name_three = items[0].value

    def path(self, items):
        #
        # could there be a way that we could get a windows path when we don't want? or 
        # a posix path in error when we don't know what to return? can't think of a way.
        #
        sep = self.ref.sep
        p = sep.join(str(item.value) for item in items)
        self.ref.name_one = p
        return p

    def fingerprint(self, items):
        #
        # need to set ref flag to say name_two not allowed because
        # fingerprint. otherwise we won't have that info later on
        # because name and fingerprint are both just strings.
        #
        f = None
        if items is not None and len(items) > 0:
            f = items[0].value
            self.ref.name_one = f
            self.ref.name_one_is_fingerprint = True
            self.seq.append("fingerprint")
        return str(f)

    def files_type(self, items):
        self.ref.datatype = "files"

    def csvpaths_type(self, items):
        self.ref.datatype = "csvpaths"

    def results_type(self, items):
        self.ref.datatype = "results"

    def reference_type(self, items):
        self.ref.datatype = "variables"

    def csvpath_type(self, items):
        self.ref.datatype = "csvpath"

    def headers_type(self, items):
        self.ref.datatype = "headers"

    def header_name(self, items):
        self.ref.name_one = items[0].value

    def variables_type(self, items):
        self.ref.datatype = "variables"

    def metadata_type(self, items):
        self.ref.datatype = "metadata"

    def INTEGER(self, item) -> int:
        return int(item)

    def DATETIME(self, item) -> str:
        return f"{item}"

    # ============================
    # tokens
    #

    def index(self, item) -> int:
        return f":{item[0]}"

    def point(self, item) -> int:
        return f"{item[0]}"

    def today(self, item) -> int:
        return ":today"

    def yesterday(self, item) -> int:
        return ":yesterday"

    def all(self, item) -> int:
        return ":all"

    def first(self, item) -> int:
        return ":first"

    def last(self, item) -> int:
        return ":last"

    def before(self, item) -> int:
        return ":before"

    def after(self, item) -> int:
        return ":after"

    def ffrom(self, item) -> int:
        return ":from"

    def to(self, item) -> int:
        return ":to"

    def data(self, item) -> int:
        return ":data"

    def unmatched(self, item) -> int:
        return ":unmatched"

    def token(self, item) -> list:
        return item[0] if item and isinstance(item, list) else item

    def tokens(self, items) -> list:
        if isinstance(items, list):
            return items
        return items.children
