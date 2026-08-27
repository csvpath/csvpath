from ...reference_3 import Reference3
from ..function_3 import Function3


class Host3(Function3):
    #
    # Table 2 (Named-File Arrivals Manifest)/Table 4 (Named-Paths Loads
    # Manifest)'s own "ip_address" field -- currently always null in
    # practice (Metadata.__init__ sets self.ip_address = None; the
    # socket.gethostbyname() lookup that would populate it is
    # commented out, found to block for seconds in some environments --
    # confirmed against metadata.py, not assumed). The field still
    # exists in both ledgers, so it still needs an accessor per
    # compendium 5.7, even though it never has a real value today.
    # Genuinely ledger-only for FILES/CSVPATHS -- neither Table 1 nor
    # Table 3 has this field at all, confirmed against file_registrar.
    # py/paths_registrar.py. RESULTS is deliberately excluded: Table 5's
    # own "ip_address" is explicitly deprecated ("Do not use", no
    # References v3 Function at all) -- see #hostname_3.py for the
    # separate, unrelated "hostname" field/function, which this is NOT
    # a rename of (a doc row appeared to suggest that, but was a
    # copy-paste artifact off this field's own row -- confirmed with
    # David, 2026-08-26).
    #
    NAME = "host"
    SUMMARY = (
        "The IP address of the process that registered a named-file "
        "version or loaded a named-paths version, from the arrivals/"
        "loads ledger only. Currently always None in practice -- the "
        "lookup that would populate this field is disabled."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {}
    LEDGER_KEY = {
        Reference3.FILES: "ip_address",
        Reference3.CSVPATHS: "ip_address",
    }
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
    }
