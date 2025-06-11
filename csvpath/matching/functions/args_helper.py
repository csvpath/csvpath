from typing import Any
import datetime
from csvpath.matching.functions.function import Function
from csvpath.matching.productions import Variable, Header, Reference, Term
from csvpath.matching.util.expression_utility import ExpressionUtility


class ArgumentValidationHelper:
    def validate(self, args_definition, actual_values, function_name):
        error_messages = []
        valid_argsets = self._find_valid_argsets(args_definition, actual_values)
        if len(valid_argsets) == 0:
            if len(args_definition.argsets) == 1:
                i = 0
                for a in args_definition.argsets[0].args:
                    if not a.is_noneable:
                        i += 1
                expected = len(args_definition.argsets[0].args)
                if i < expected:
                    return f"{function_name}() requires {i} to {expected} argument{'s' if expected != 1 else ''}"
                else:
                    return f"{function_name}() requires {expected} argument{'s' if expected != 1 else ''}"
            return self._get_argument_count_error(function_name, args_definition)
        #
        # Validate each argument against the argset.
        # this part gets ugly. we should instead just say:
        #   f"invalid {argset.matchable.name}. {argset.explain}"
        # and then write the explanation into the classes. (OMG! but it would be best, imho).
        #
        results = []
        for va in valid_argsets:
            #
            # in the rare cases where arg.actuals is [] we don't validate.
            # presumably the intent would be to accept any values coming from
            # the expected types of match components. reset_headers()
            # and empty() are examples of []. not sure if good examples. []
            # should probably be avoided.
            #
            for i, actual in enumerate(actual_values):
                #
                # va args can be less than i. we assume that means
                # actual must == the valid argset's last arg in the ith
                # position.
                #
                arg_def = None
                if i >= len(va.args):
                    arg_def = va.args[len(va.args) - 1]
                else:
                    arg_def = va.args[i]
                error = self._validate_argument(actual, arg_def, i)
                if error:
                    error_messages.append(f"{function_name} {error}")
            if len(error_messages) == 0:
                return None
            results.append(". ".join(error_messages))
            error_messages = []
        results = self._dedup(results)
        ret = None
        if len(results) > 1:
            ret = " or ".join(results)
        else:
            ret = f"{results[0]}"
        return ret

    def _find_valid_argsets(self, args, actual_values):
        valid_argsets = []
        for argset in args.argsets:
            if argset.max_length == -1:
                valid_argsets.append(argset)
            elif len(argset.args) == len(actual_values):
                valid_argsets.append(argset)
            elif argset.min_length <= len(actual_values) and argset.max_length >= len(
                actual_values
            ):
                valid_argsets.append(argset)
        return valid_argsets

    def _validate_argument(self, actual_value, arg_def, position):
        # this case is unusual, but happens. we don't validate.
        if len(arg_def.actuals) == 0:
            return None
        # Check if value can be None
        p1 = position + 1
        if actual_value is None and None not in arg_def.actuals:
            if arg_def.is_noneable:
                return f"requires a value for argument {p1} or no {p1}{self._th(p1)} argument"
            else:
                return f"requires a value for argument {p1}"

        # Check actual type against allowed types
        if actual_value is not None:
            actual_type = type(actual_value)
            a = Any not in arg_def.actuals
            b = actual_type not in arg_def.actuals
            c = not ExpressionUtility.is_one_of(actual_value, arg_def.actuals)
            if a and b and c:
                expected = self._format_expected_types(arg_def.actuals)
                return f"requires {expected} for argument {p1}"
        return None

    def _format_expected_types(self, allowed_types):
        type_names = []
        for t in allowed_types:
            if t == int:
                type_names.append("an integer")
            elif t == str:
                type_names.append("a string")
            elif t == float:
                type_names.append("a decimal")
            elif t == datetime.datetime:
                type_names.append("a datetime")
            elif t == datetime.date:
                type_names.append("a date")
            elif t == bool:
                type_names.append("a boolean")
            #
            # Add more type mappings as needed
            #
        if len(type_names) == 1:
            return type_names[0]
        return f"one of: {', '.join(type_names)}"

    def _get_argument_count_error(self, function_name, args_definition):
        possibilities = []
        for argset in args_definition.argsets:
            if argset.max_length == -1:
                return f"{function_name} accepts any number of arguments"
            possibilities.append(str(len(argset.args)))

        if len(possibilities) == 1 or self._all_same(possibilities):
            return f"{function_name} requires {possibilities[0]} arguments"
        return f"{function_name} requires {' or '.join(possibilities)} arguments"

    # =============
    # helpers
    # =============

    def _dedup(self, poss: list[str]) -> list[str]:
        us = []
        [us.append(x) for x in poss if x not in us]
        return us

    def _all_same(self, poss: list) -> bool:
        a = poss[0]
        for i, b in enumerate(poss):
            if i == 0:
                continue
            if b != a:
                return False
        return True

    def _th(self, i: int) -> str:
        if i == 1:
            return "st"
        if i == 2:
            return "nd"
        if i == 3:
            return "rd"
        else:
            return "th"
