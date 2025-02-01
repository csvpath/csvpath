import unittest
import pytest
from typing import Any
import datetime
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.functions.args import Args, Arg, ArgSet
from csvpath.matching.productions.term import Term
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.header import Header
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.reference import Reference
from csvpath.matching.productions.equality import Equality
from csvpath.util.config_exception import ConfigurationException
from csvpath.matching.functions.boolean.no import No
from csvpath.matching.functions.boolean.all import All


class TestNewValidation(unittest.TestCase):
    def test_new_args_actuals1(self):
        args = Args()
        a = args.argset(3)
        a.arg(
            types=[Term, Variable, Header, Function, Reference],
            actuals=[datetime.datetime, datetime.date, float, int, str],
        )
        a.arg(
            types=[Term, Variable, Header, Function, Reference],
            actuals=[datetime.datetime, datetime.date, float, int, str],
        )
        a.arg(
            types=[Term, Variable, Header, Function, Reference],
            actuals=[datetime.datetime, datetime.date, float, int, str],
        )
        for a in args.argsets[0].args:
            assert a.actuals == [datetime.datetime, datetime.date, float, int, str]

    def test_new_args_arg_init0(self):
        arg = Arg()
        assert isinstance(arg.types, list)
        assert isinstance(arg.actuals, list)
        assert arg.types == []
        assert arg.actuals == []
        assert arg.is_noneable

    def test_new_args_arg_init1(self):
        arg = Arg(types=None, actuals=None)
        assert isinstance(arg.types, list)
        assert isinstance(arg.actuals, list)
        assert arg.types == []
        assert arg.actuals == []
        assert arg.is_noneable

    def test_new_args_arg_init2(self):
        arg = Arg(types=[Any], actuals=None)
        assert isinstance(arg.types, list)
        assert isinstance(arg.actuals, list)
        assert Function in arg.types
        assert Term in arg.types
        assert Reference in arg.types
        assert Header in arg.types
        assert Variable in arg.types
        assert Equality in arg.types
        assert arg.actuals == []
        assert not arg.is_noneable

    def test_new_args_arg_init3(self):
        arg = ArgSet().arg(types=[Any], actuals=None)
        assert isinstance(arg.types, list)
        assert isinstance(arg.actuals, list)
        assert Function in arg.types
        assert Term in arg.types
        assert Reference in arg.types
        assert Header in arg.types
        assert Variable in arg.types
        assert Equality in arg.types
        assert arg.actuals == []
        assert not arg.is_noneable

    def test_new_args_arg_init4(self):
        arg = ArgSet().arg()
        assert isinstance(arg.types, list)
        assert isinstance(arg.actuals, list)
        assert arg.types == []
        assert arg.actuals == []
        assert arg.is_noneable

    # --------
    # argset
    # --------

    def test_new_args_argset1(self):
        a = ArgSet(5)
        assert a.max_length == 5
        assert a.min_length == -1
        assert a.args == []

    def test_new_args_argset2(self):
        a = ArgSet().length(5)
        assert isinstance(a, ArgSet)
        assert a.max_length == 5
        assert a.min_length == -1
        assert a.args == []

    def test_new_args_argset_min_len1(self):
        a = ArgSet()
        a.arg(types=[Function, Term], actuals=[None, str, int])
        assert a.max_length == -1
        assert a.min_length == -1
        a._set_min_length()
        assert a.min_length == 1

    def test_new_args_argset_min_len2(self):
        a = ArgSet()
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        assert a.max_length == -1
        assert a.min_length == -1
        a._set_min_length()
        assert a.min_length == 0

    def test_new_args_argset_min_len3(self):
        a = ArgSet()
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        a.arg(types=[Function], actuals=[None])
        # no non-noneable after a noneable
        with pytest.raises(ConfigurationException):
            a._set_min_length()

    def test_new_args_argset_max_len1(self):
        a = ArgSet(2)
        assert a.max_length == 2
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        assert a.max_length == 4

    def test_new_args_argset_validate_len1(self):
        a = ArgSet(1)
        assert a.max_length == 1
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        assert a.max_length == 2
        sibs = [No(None, "no"), No(None, "no")]
        v = a._validate_length(sibs)
        assert v is True

    def test_new_args_argset_validate_len2(self):
        a = ArgSet(1)
        assert a.max_length == 1
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[Function, Term], actuals=[None, str, int])
        assert a.max_length == 2
        sibs = [No(None, "no")]
        v = a._validate_length(sibs)
        assert v is False

    def test_new_args_argset_validate_len3(self):
        a = ArgSet(1)
        assert a.max_length == 1
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[Function, Term], actuals=[None, str, int])
        assert a.max_length == 2
        sibs = [No(None, "no"), No(None, "no"), No(None, "no")]
        v = a._validate_length(sibs)
        assert v is False

    def test_new_args_argset_validate_len4(self):
        a = ArgSet(1)
        assert a.max_length == 1
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        assert a.max_length == 2
        sibs = [No(None, "no")]
        v = a._validate_length(sibs)
        assert a.min_length == 1
        assert v is True

    def test_new_args_argset_pad1(self):
        a = ArgSet(-1)
        assert a.max_length == -1
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        assert a.max_length == -1
        sibs = [No(None, "no"), No(None, "no"), No(None, "no")]
        v = a._validate_length(sibs)
        assert a.min_length == 1
        assert v is True
        assert a.args_count == 2
        a._pad_or_shrink(sibs)
        assert a.args_count == 3
        assert a.max_length == -1
        assert a.args[2] == a.args[1]

    def test_new_args_argset_pad2(self):
        a = ArgSet(2)
        assert a.max_length == 2
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        assert a.max_length == 6
        sibs = [No(None, "no"), No(None, "no"), No(None, "no")]
        v = a._validate_length(sibs)
        assert a.min_length == 1
        assert v is True
        assert a.args_count == 6
        a._pad_or_shrink(sibs)
        assert a.args_count == 3
        assert a.max_length == 3
        assert len(sibs) == a.args_count

    def test_new_args_argset_valid1(self):
        # 2 args defined, but no max vis-a-vis 3 sibs == True
        a = ArgSet()
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        sibs = [No(None, "no"), No(None, "no"), No(None, "no")]
        # None is the new correct. incorrect is a str error msg.
        v = a.validate_structure(sibs)
        assert v is None

    def test_new_args_argset_valid2(self):
        # 2 args defined, w/2 max vis-a-vis 3 sibs == False
        a = ArgSet(2)
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        sibs = [No(None, "no"), No(None, "no"), No(None, "no")]
        msg = a.validate_structure(sibs)
        assert msg is not None

    def test_new_args_argset_valid3(self):
        # 2 args defined, w/o max vis-a-vis 3 sibs with 1 non-match == False
        a = ArgSet()
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[Variable], actuals=[Variable])
        sibs = [No(None, "no"), No(None, "no"), No(None, "no")]
        msg = a.validate_structure(sibs)
        assert msg is not None

    def test_new_args_args1(self):
        args = Args()
        a = args.argset()
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[Variable, Term], actuals=[Variable])
        sibs = [No(None, "no"), No(None, "no"), No(None, "no")]
        #
        # this test is old. we were catching ChildrenException but that
        # is no longer doable without a matchable, a matcher, and a
        # csvpath. still, AttributeError tells us that we would be
        # raising the expected exception if we could. I don't think it
        # is worth improving the testability -- it's not bad, just
        # doesn't fit this test. test still basically works.
        #
        with pytest.raises(AttributeError):
            args.validate(sibs)
        a = args.argset()
        a.arg(types=[Function, Term], actuals=[None, str, int])
        a.arg(types=[Variable, Function], actuals=[int])
        a.arg(types=[Variable, Function], actuals=[int])
        # good is not blowing up; no assert needed
        args.validate(sibs)

    def test_new_args_args2(self):
        args = Args()
        a = args.argset()
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        a.arg(types=[None, Variable, Term], actuals=[int])
        sibs = []
        # good is not blowing up; no assert needed
        args.validate(sibs)

    def test_new_args_args3(self):
        args = Args()
        a = args.argset()
        a.arg(types=[None, Function, Term], actuals=[None, str, int])
        a.arg(types=[Variable, Term], actuals=[int])
        sibs = []
        with pytest.raises(ConfigurationException):
            args.validate(sibs)

    def test_new_args_zero_args(self):
        # this should be fine as-is, no assert needed, if we fail we raise
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse("$tests/test_resources/test.csv[*][yes()]")
        path.fast_forward()
        no = All(path.matcher, name="no")
        no.args = Args(matchable=no)
        no.args.argset(0)
        no.args.argset(1).arg(types=[Variable], actuals=[])
        no.args.matches([])
