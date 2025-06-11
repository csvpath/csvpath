# pylint: disable=C0114
import re
import os

from datetime import timedelta, timezone, datetime
from csvpath.matching.util.expression_utility import ExpressionUtility
from .reference_parser import ReferenceParser

from csvpath.util.nos import Nos


class ReferenceUtility:
    @classmethod
    def results_manifest_path_to_reference(
        cls, archive_name: str, manipath: str, is_instance=True
    ) -> str:
        #
        # find the run_dir by regex. this doesn't tell us about the template and we
        # don't have the template, but we can work around that.
        #
        m = re.search(r"[/\\]\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(_\d)?[/\\]", manipath)
        if m is None:
            raise ValueError(f"Cannot find a run_dir in {manipath}")
        run_dir = m.group(0)
        instance = None
        #
        # if we're an instance manifest the caller has to tell us. simplifies things a bit.
        #
        if is_instance:
            instance = os.path.dirname(manipath)
            instance = os.path.basename(instance)
        #
        # find the archive
        #
        i = manipath.find(archive_name)
        if i == -1:
            raise ValueError(f"Cannot find the archive root in {manipath}")
        manipath = manipath[i + len(archive_name) :]
        #
        # nos will recognize if we're URL, windows, or posix
        #
        nos = Nos(manipath)
        #
        # get the named-paths name
        #
        i = manipath.find(nos.sep, 1)
        name = manipath[1:i]
        #
        # now we'll get the fully qualified run_dir path up to the run_dir. we don't
        # need the whole template-created path, any suffix included, because the progressive
        # match only needs to get to the end of the run_dir to match exactly one run.
        #
        manipath = manipath[i + 1 :]
        manipath = manipath[0 : manipath.find(run_dir) + len(run_dir) - 1]
        #
        # and we're done.
        #
        if instance is None:
            return f"${name}.results.{manipath}"
        else:
            return f"${name}.results.{manipath}.{instance}"

    @classmethod
    def by_day(cls, run_dir: str) -> str:
        pointer = cls.pointer(run_dir)
        run = cls.not_pointer(run_dir)
        if run == "today":
            ret = cls.translate_today()
            if pointer is not None:
                ret = f"{ret}:{pointer}"
        elif run == "yesterday":
            ret = cls.translate_yesterday()
            if pointer is not None:
                ret = f"{ret}:{pointer}"
        else:
            ret = run_dir
        return ret

    @classmethod
    def translate_today(cls) -> str:
        d = datetime.now().astimezone(timezone.utc)
        ret = f"{d.strftime('%Y')}-{d.strftime('%m')}-{d.strftime('%d')}_"
        return ret

    @classmethod
    def translate_yesterday(cls) -> str:
        d = datetime.now().astimezone(timezone.utc)
        d = d - timedelta(days=1)
        ret = f"{d.strftime('%Y')}-{d.strftime('%m')}-{d.strftime('%d')}_"
        return ret

    @classmethod
    def is_day(cls, name: str) -> bool:
        if name.find(":"):
            name = name[0 : name.find(":")]
        return name in ["yesterday", "today"]

    @classmethod
    def pointer(cls, name: str, default: str = None) -> str:
        #
        # pointer will return a compound or stacked pointer. in the
        # case of :today and :yesterday we allow two pointers because
        # the first -- one of those two -- is just a replacement.
        # they are not like all the other pointers in that they don't
        # decide what to return, they just stand in for a value that
        # is a PIA to create.
        #
        if name is None:
            return None
        if name.find(":") == -1:
            return default
        tn = name[name.find(":") + 1 :]
        #
        # remove any suffix. suffix can be separated by / or \
        #
        i = tn.find("/") if tn.find("/") > -1 else tn.find("\\")
        if i > -1:
            tn = tn[0:i]
        return tn

    @classmethod
    def not_pointer(cls, name: str) -> str:
        if name is None:
            return None
        i = name.find(":")
        if i == -1:
            return name
        return name[0:i]

    @classmethod
    def bare_index_if(cls, name: str) -> int | None:
        if name is None:
            return None
        name = name.strip()
        if name[0] != ":":
            return None
        name = name[1:]
        if not ExpressionUtility.is_number(name):
            return None
        name = ExpressionUtility.to_int(name)
        if isinstance(name, int):
            return name
        return None
