from ...reference_3 import Reference3
from ..function_3 import Function3


class Host3(Function3):
    #
    # Consolidated 2026-09-20 from two separate functions, Host3 (this
    # class, formerly the accessor for Table 2/Table 4's "ip_address"
    # field) and Hostname3 (formerly the accessor for the real,
    # populated "hostname" field: Table 5 directly for RESULTS, Table 2/
    # Table 4's arrivals/loads ledgers for FILES/CSVPATHS -- neither
    # Table 1 nor Table 3 has "hostname" on the entity's own manifest).
    #
    # The two functions existed separately because they modeled two
    # genuinely different fields. That distinction is retired on
    # purpose, not by mistake: "ip_address" is confirmed always-null in
    # practice (the socket.gethostbyname() lookup that would populate it
    # is disabled, per metadata.py) and is not expected to become useful
    # -- David, 2026-09-20, reconsidering the original design with that
    # in mind, not overturning it blindly. One function, "host", now
    # covers the one field worth exposing. "ip_address" itself keeps no
    # accessor at all (manifest doc: "Do not use").
    #
    # This is the second time this exact question was asked -- see the
    # 2026-08-26 note (superseded by this one, kept in git history on
    # this class) confirming Host3/Hostname3 were NOT the same function.
    # That confirmation was correct for the design as it stood then; the
    # design itself changed here, which is a different thing from
    # reversing a mistake. If a fourth round happens, the two real
    # fields this once modeled were "ip_address" (Table 2/Table 4,
    # always null) and "hostname" (Table 5 direct; Table 2/Table 4
    # ledger-only for FILES/CSVPATHS).
    #
    NAME = "host"
    SUMMARY = (
        "The hostname of the machine that performed the resolved "
        "action -- registered/loaded a named-file/named-paths version "
        "(via the arrivals/loads ledger only), or executed a results "
        "run (directly on the run's own manifest)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "hostname",
    }
    LEDGER_KEY = {
        Reference3.FILES: "hostname",
        Reference3.CSVPATHS: "hostname",
    }
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
