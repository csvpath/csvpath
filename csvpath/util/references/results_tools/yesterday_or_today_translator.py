from csvpath.util.references.ref_utils import ReferenceUtility as refu


class YesterdayOrTodayTranslator:
    # finder: "ResultsReferenceFinder2" disallowed by flake
    #  -> "ReferenceResults" disallowed by flake
    @classmethod
    def update(cls, *, refstr, finder):
        today = refu.translate_today()
        n_refstr = refstr.replace(":today", today)
        yesterday = refu.translate_yesterday()
        n_refstr = n_refstr.replace(":yesterday", yesterday)
        return finder.resolve(refstr=n_refstr)
