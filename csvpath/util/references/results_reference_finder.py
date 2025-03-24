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

    def resolve(self, refstr: str = None, with_instance=True) -> str:
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
        pointer = refu.pointer(name)
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
        # handle pointer, if any
        #
        resolved = None
        if len(possibles) == 0:
            ...
        if len(possibles) == 1:
            resolved = possibles[0]
        elif pointer is not None and pointer.strip() != "" and len(possibles) > 0:
            #
            # time order the possibles
            #
            ps = {os.path.dirname(p): p for p in possibles}
            keys = list(ps.keys())
            keys.sort()
            possibles = [ps[k] for k in keys]
            #
            # do the pointer
            #
            if pointer == "last":
                resolved = possibles[len(possibles) - 1]
            elif pointer == "first":
                resolved = possibles[0]
            else:
                i = ExpressionUtility.to_int(pointer)
                if not isinstance(i, int):
                    raise ValueError(f"Pointer :{pointer} is not recognized")
                elif i < len(possibles):
                    resolved = possibles[i]
        if resolved is not None and with_instance is True:
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
            if not any(other.startswith(string) for other in result):
                result.append(string)
        return result
