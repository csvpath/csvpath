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
    # this is the public api. everything else is private
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
        #
        # done!! :)
        #
        return resolved

    def _filter_prefixes(self, possibles: list[str]) -> list[str]:
        possibles.sort()  # alpha sort to group prefixes
        possibles.sort(key=len, reverse=True)  # Sort by length, longest first
        result = []
        for string in possibles:
            if not any(other.startswith(string) for other in result):
                result.append(string)
        return result

    #
    # ============= REMOVE! OLD, SORTA WORKING BUT NO LONGER USED =================
    #
    def run_home_for_reference(self, refstr, not_name: str = None) -> str:
        ref = ReferenceParser(refstr)
        if ref.datatype != ReferenceParser.RESULTS:
            raise ValueError(f"Reference datatype must be {ReferenceParser.RESULTS}")
        namedpaths = ref.root_major
        instance = ref.name_one
        #
        # we can look for yesterday:first or today:last type name_ones here and replace with
        # the approprate partial date-based run dir name.
        #
        instance = refu.by_day(instance)
        #
        # not used? why? this is selector2 in: $named-results-name.results.selector1.selector2
        # not yet needed for results identification.
        #
        base = self._csvpaths.config.archive_path
        filename = os.path.join(base, namedpaths)
        if not Nos(filename).dir_exists():
            raise ValueError(
                f"Reference {refstr} resolved to {filename} that is not a named-paths group with at least 1 run"
            )
        #
        # instance can have pointers like:
        #   2024-01-01_10-15-:last
        #   2024-01-01_10-:first
        #   2024-01-01_10:0
        #
        instance = self._find_instance(
            filename, instance, not_name=not_name, name_three=ref.name_three
        )
        #
        # prefix and suffix are any template-driven dirnames around the instance.
        # we need to rewrap the instance with them.
        #
        suffix = ""
        s = ref.name_one.find("/", ref.name_one.rfind("-"))
        if s == -1:
            s = ref.name_one.find("\\", ref.name_one.rfind("-"))
        if s > -1:
            suffix = ref.name_one[s:]
        #
        #
        #
        prefix = ""
        p = ref.name_one.find("/", 0, s - 1)
        if p == -1:
            p = ref.name_one.find("\\", 0, s - 1)
        if p > -1:
            prefix = ref.name_one[0 : p + 1]
        filename = f"{filename}{os.sep}{prefix}{instance}{suffix}"
        #
        # this doubled base showed up as a problem in Cli during replay. it likely stems
        # from a difference between a :last/:first ref vs. just a plan run name. would
        # be nice to try buffing it out, but atm it's fine.
        #
        if not Nos(filename).dir_exists():
            raise ValueError(
                f"Reference {refstr} does not point to a valid named-paths run file at {filename}"
            )
        return filename

    def instance_home_for_reference(
        self, refstr: str = None, not_name: str = None
    ) -> str:
        filename = self.run_home_for_reference(refstr, not_name=not_name)
        ref = ReferenceParser(refstr)
        if ref.datatype != ReferenceParser.RESULTS:
            raise ValueError(f"Reference datatype must be {ReferenceParser.RESULTS}")
        filename = os.path.join(filename, ref.name_three)
        if not Nos(filename).dir_exists():
            raise ValueError(
                f"Reference to {filename} does not point to a csvpath in a named-paths group run"
            )
        return filename

    #
    # ===============================================
    #
    # ===============================================
    #

    def _find_instance(
        self, filename, instance, not_name: str = None, name_three: str = None
    ) -> str:
        c = instance.find(":")
        if c == -1:
            filename = os.path.join(filename, instance)
            return filename
        suffix = ""
        # should be rfind?
        s = (
            instance.find("/", c)
            if instance.find("/", c) > -1
            else instance.find("\\", c)
        )
        if s > -1:
            suffix = instance[s:]
            instance = instance[0:s]
        #
        # any impact from cloud blob dir handling?
        #
        if not Nos(filename).dir_exists():
            raise ValueError(f"The base dir {filename} must exist")

        var = instance[c:]
        instance = instance[0:c]
        ret = None
        if var == ":last":
            ret = self._find_last(
                filename,
                instance,
                not_name=not_name,
                name_three=name_three,
                suffix=suffix,
            )
        elif var == ":first":
            ret = self._find_first(
                filename,
                instance,
                not_name=not_name,
                name_three=name_three,
                suffix=suffix,
            )
        else:
            raise ValueError(f"Unknown reference pointer: {var}")
        return f"{ret}{suffix}"

    def _find_last(
        self,
        filename,
        instance,
        not_name: str = None,
        name_three: str = None,
        suffix=None,
    ) -> str:
        last = True
        return self._find(
            filename,
            instance,
            last,
            not_name=not_name,
            name_three=name_three,
            suffix=suffix,
        )

    def _find_first(
        self,
        filename,
        instance,
        not_name: str = None,
        name_three: str = None,
        suffix=None,
    ) -> str:
        first = False
        return self._find(
            filename,
            instance,
            first,
            not_name=not_name,
            name_three=name_three,
            suffix=suffix,
        )

    def _find(
        self,
        filename,
        instance,
        last: bool = True,
        not_name: str = None,
        name_three: str = None,
        suffix: str = None,
    ) -> str:
        pre = None
        _p = instance.find("/")
        if _p > -1:
            pre = instance[0:_p]
            instance = instance[_p + 1 :]
        _p = instance.find("\\")
        if _p > -1:
            pre = instance[0:_p]
            instance = instance[_p + 1 :]
        if pre is not None:
            filename = os.path.join(filename, pre)
        names = Nos(filename).listdir()
        ns = []
        for i, n in enumerate(names):
            if not_name is not None and not_name.endswith(n):
                continue
            if n.startswith("."):
                continue
            #
            # test for manifest existing here?
            #
            #
            # might we not just have a method that finds a manifest? below this dir, all dir subtrees
            # should have a manifest. the question isn't is there a manifest, the question is, what is
            # the subtree that gets us to it.
            #
            mani = os.path.join(filename, n)
            if suffix is not None:
                mani = f"{mani}{suffix}"
            mani = os.path.join(mani, "manifest.json")
            if not Nos(mani).exists():
                continue
            else:
                #
                # load mani and check for time_completed
                #
                with DataFileReader(mani) as file:
                    j = json.load(file.source)
                    if "time_completed" not in j or j["time_completed"] is None:
                        continue
            if name_three:
                mani = os.path.join(filename, n)
                if suffix is not None:
                    mani = f"{mani}{suffix}"
                mani = os.path.join(mani, name_three)
                mani = os.path.join(mani, "manifest.json")
                if not Nos(mani).exists():
                    continue
            ns.append(n)
        #
        #
        #
        ret = self._find_in_dir_names(instance, ns, last)
        return ret

    def _find_in_dir_names(self, instance: str, names, last: bool = True) -> str:
        ms = "%Y-%m-%d_%H-%M-%S_%f"
        s = "%Y-%m-%d_%H-%M-%S"
        names = [n for n in names if n.startswith(instance)]
        if len(names) == 0:
            return None
        #
        # change from . to _ requires change from find to count
        #
        names = sorted(
            names,
            key=lambda x: datetime.strptime(x, ms if x.count("_") > 1 else s),
        )
        if last is True:
            i = len(names)
            #
            # we drop 1 because -1 for the 0-base. note that we may find a replay
            # run that doesn't have the asset we're looking for. that's not great
            # but it is fine -- the rule is, no replays of replays using :last.
            # it is on the user to set up their replay approprately.
            #
            i -= 1
            if i < 0:
                self.csvpaths.logger.error(
                    f"Previous run is at count {i} but there is no such run. Returning None."
                )
                self.csvpaths.logger.info(
                    "Found previous runs: %s matching instance: %s", names, instance
                )
                return None
            ret = names[i]
        else:
            ret = names[0]
        return ret
