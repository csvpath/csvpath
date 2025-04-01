# pylint: disable=C0114
import os
import json
from datetime import datetime
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..template_util import TemplateUtility as temu
from ..nos import Nos
from ..file_readers import DataFileReader
from .reference_parser import ReferenceParser
from .files_reference_finder import FilesReferenceFinder
from .ref_utils import ReferenceUtility as refu


class ResultsReferenceFinder:
    def __init__(self, csvpaths, *, ref: ReferenceParser = None, name=None) -> None:
        self._csvpaths = csvpaths
        self._name = name
        self._ref = None
        if self._name is not None:
            if ref is not None:
                raise ValueError("Cannot provide both ref and name")
            self._ref = ReferenceParser(name)
        if self._ref is None:
            self._ref = ref

    def get_file_manifest_entry_for_results_reference(self) -> dict:
        home = self.resolve(with_instance=False)
        mpath = os.path.join(home, "manifest.json")
        mani = None
        with DataFileReader(mpath) as reader:
            mani = json.load(reader.source)
        file = mani["named_file_path"]
        nfn = mani["named_file_name"]
        if nfn.startswith("$"):
            ref = ReferenceParser(nfn)
            if ref.datatype == ref.FILES:
                # file ref? use files_refer_finder.get_manifest_entry_for_reference
                return FilesReferenceFinder(
                    self._csvpaths, name=nfn
                ).get_manifest_entry_for_reference()
            elif ref.datatype == ref.RESULTS:
                # results ref? use this method recursively
                return ResultsReferenceFinder(
                    self._csvpaths, name=nfn
                ).get_file_manifest_entry_for_results_reference()
        else:
            # plain nfn? do this:
            mani = self._csvpaths.file_manager.get_manifest(nfn)
            for _ in mani:
                if _["file"] == file:
                    return _
        raise ValueError(
            f"Cannot match reference {self.ref._ref_string} pointing to file {file} to a manifest entry"
        )

    #
    # this is the public api:
    #
    #   - get_file_manifest_entry_for_results_reference()
    #   - resolve()
    #   - resolve_possibles()
    #
    # =========================================
    #
    # we need to handle references like:
    #
    #    $myruns.results.2025-03-01_00-00-00_2
    #    $myruns.results.2025-03:first
    #    $myruns.results.2025-03:last
    #    $myruns.results.2025-03:4
    #    $myruns.results.:today:first
    #    $myruns.results.:today:last
    #    $myruns.results.:today:4
    #    $myruns.results.:yesterday:first
    #    $myruns.results.:yesterday:last
    #    $myruns.results.:yesterday:4
    #    $myruns.results.:first
    #    $myruns.results.:last
    #    $myruns.results.:4
    #
    # our results may have templates:
    #
    #    $myruns.results.acme/orders/2025-03/final:first
    #
    # where the template was ":2/:1/:run_dir/final"
    #
    # references may take a "name_three" name that is the last
    # part of a reference following the third dot.
    #
    #    $myruns.results.acme/orders/2025-03/final:first.add_header
    #
    # where add_header is an instance (a csvpath) in the
    # named-paths group myruns.
    #
    # basically, to find the run_dir or an instance dir (a.k.a.
    # run home and instance home) we:
    #
    #   - find the template prefix and suffix
    #   - use the prefix to find the location of the runs
    #   - use progressive match to find the possible runs
    #   - if multiple possibles, use a pointer or raise an exception
    #   - if there is a name_three instance identity, include it
    #

    def resolve_possibles(self, refstr: str = None, with_instance=True) -> str:
        if refstr is None:
            refstr = self._name
        if refstr is None:
            raise ValueError("Must pass in a reference string on init or this method")
        ref = ReferenceParser(refstr)
        name = ref.name_one
        #
        # find suffix. count separators. trim suffix from refstr
        #
        suffix = temu.get_template_suffix(csvpaths=self._csvpaths, ref=refstr)
        c = suffix.count("/")
        while c > 0:
            r = name.rfind("/")
            name = name[0:r]
            c -= 1
        #
        # find all possible dir path matches
        #
        name_home = self._csvpaths.results_manager.get_named_results_home(
            ref.root_major
        )
        possibles = Nos(name_home).listdir(
            recurse=True, files_only=False, dirs_only=True
        )
        #
        # swap out 'today' and 'yesterday'
        #
        today = refu.translate_today()
        name = name.replace(":today", today)
        yesterday = refu.translate_yesterday()
        name = name.replace(":yesterday", yesterday)
        #
        # extract pointer, if any
        #
        name = refu.not_pointer(name)
        #
        # filter possibles. last level should be instances. remove those.
        #
        looking_for = os.path.join(name_home, name)
        possibles = [
            p[0 : len(os.path.dirname(p))]
            for p in possibles
            if p.startswith(looking_for)
        ]
        possibles = list(set(possibles))
        ps = []
        #
        # keep only longest of any strings having a common prefix.
        #
        possibles = self._filter_prefixes(possibles)
        #
        # sort possibles
        #
        if len(possibles) < 2:
            return possibles
        ps = {os.path.basename(p): p for p in possibles}
        keys = list(ps.keys())
        keys.sort()
        possibles = [ps[k] for k in keys]
        return possibles

    def resolve(self, refstr: str = None, with_instance=True) -> str:
        if refstr is None:
            refstr = self._name
        if refstr is None:
            raise ValueError("Must pass in a reference string on init or this method")
        ref = ReferenceParser(refstr)
        name = ref.name_one
        possibles = self.resolve_possibles(refstr, with_instance)
        resolved = None
        pointer = refu.pointer(name)
        if (
            pointer
            and pointer.find(":") > -1
            and (pointer.startswith("today") or pointer.startswith("yesterday"))
        ):
            pointer = refu.pointer(pointer)
        name = refu.not_pointer(name)
        #
        # do the pointer
        #
        i = ExpressionUtility.to_int(pointer)
        if pointer == "last":
            resolved = possibles[len(possibles) - 1]
        elif pointer == "first":
            resolved = possibles[0]
        elif not isinstance(i, int):
            raise ValueError(f"Pointer :{pointer} is not recognized")
        elif i < len(possibles):
            resolved = possibles[i]
        #
        # ideally, maybe?, if resolved is None and len(possibles) > 0 return
        # the top possible, which should be the nearest possible to the time
        # indicated or the first path found if there are multiple path prefixes
        # due to a template. otoh, I'm not 100% convinced I'm right about that
        # approach. any way you think about it, returning multiple results is
        # not great and returning a single result when multiple match has the
        # chance of confusing the user and or giving them a bug. for now, just
        # taking a wait and see -- and returning None
        #
        if (
            resolved is not None
            and with_instance is True
            and ref.name_three is not None
        ):
            #
            # add instance name?
            #
            resolved = os.path.join(resolved, ref.name_three)
        return resolved

    def _filter_prefixes(self, possibles: list[str]) -> list[str]:
        possibles.sort()  # alpha sort to group prefixes
        possibles.sort(key=len, reverse=True)  # Sort by length, longest first
        result = []
        for string in possibles:
            if not any(self._trailing(string, other) for other in result):
                # if not any(other.startswith(string) for other in result):
                result.append(string)
        return result

    def _trailing(self, candidate: str, other: str) -> bool:
        if not other.startswith(candidate):
            return False
        #
        # looking for matches like: 2025-01-01_00-01-05 vis-a-vis 2025-01-01_00-01-05_01
        # if we see those we like them both because both are separate runs, even though
        # their paths/names overlap
        #
        r = other[len(candidate) :]
        if r[0] != "_" or len(r) == 1:
            return True
        r = r[1:]
        i = ExpressionUtility.to_int(r)
        if isinstance(i, int):
            return False
        return True
