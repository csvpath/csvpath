import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_expression_parser_3 import (
    ReferenceExpressionParser3 as Parser,
)

#
# issue #444: the written form of a reference expression. Rulings, David
# 2026-11-15: operators are case-insensitive, and more than one operator
# at one level needs grouping parentheses.
#
A = "$a.files.:last()"
B = "$b.results.:last():identity()"
C = "$c.csvpaths.:first()"


class TestSplit:
    def test_a_plain_reference_is_one_part(self):
        assert Parser.split(A) == [A]

    def test_one_operator_is_three_parts(self):
        assert Parser.split(f"{A} UNION {B}") == [A, "union", B]

    def test_operators_are_case_insensitive(self):
        for op in ("UNION", "union", "Union", "INTERSECT", "subtract"):
            assert Parser.split(f"{A} {op} {B}")[1] == op.lower()

    def test_extra_whitespace_is_stripped(self):
        assert Parser.split(f"  {A}\t  intersect\n {B}  ") == [A, "intersect", B]

    def test_an_operator_inside_a_quoted_string_does_not_split(self):
        ref = '$a.files.:regex("x UNION y")'
        assert Parser.split(ref) == [ref]
        assert Parser.split(f"{ref} UNION {B}") == [ref, "union", B]

    def test_an_escaped_quote_stays_inside_the_string(self):
        ref = r'$a.files.:name("say \" UNION ")'
        assert Parser.split(ref) == [ref]

    def test_an_operator_inside_a_regex_does_not_split(self):
        ref = "$a.files.:name(/x UNION y/)"
        assert Parser.split(ref) == [ref]

    def test_a_paren_inside_a_regex_is_not_counted(self):
        ref = "$a.files.:name(/^a (b/)"
        assert Parser.split(f"{ref} UNION {B}") == [ref, "union", B]

    def test_a_quote_inside_a_regex_is_not_a_string(self):
        ref = '$a.files.:name(/a"b/)'
        assert Parser.split(f"{ref} UNION {B}") == [ref, "union", B]

    def test_an_escaped_slash_stays_inside_the_regex(self):
        ref = r"$a.files.:name(/x\/ UNION y/)"
        assert Parser.split(ref) == [ref]

    def test_whitespace_before_a_regex_arg_still_starts_a_regex(self):
        ref = "$a.files.:regex( /x) UNION y/ )"
        assert Parser.split(f"{ref} UNION {B}") == [ref, "union", B]

    def test_a_quoted_operator_inside_a_nested_function_does_not_split(self):
        ref = '$acme.results.:last().*:having(:identity("x UNION y"))'
        assert Parser.split(f"{ref} UNION {B}") == [ref, "union", B]

    def test_only_grammar_whitespace_bounds_an_operator(self):
        # the grammar's WS is space, tab, form feed, CR and LF; a
        # non-breaking space is not one, so no split here
        ref = "$a.files.x union\xa0$b.files.y"
        assert Parser.split(ref) == [ref]

    def test_a_path_slash_is_not_a_regex(self):
        ref = "$a.results.:all()/:regex(/01-01/)"
        assert Parser.split(f"{ref} UNION {B}") == [ref, "union", B]

    def test_a_word_containing_an_operator_is_not_one(self):
        ref = "$unions.files.reunion"
        assert Parser.split(ref) == [ref]
        assert Parser.split("$a.files.x_union_y") == ["$a.files.x_union_y"]

    def test_an_operator_inside_a_group_is_not_top_level(self):
        assert Parser.split(f"({A} UNION {B}) SUBTRACT {C}") == [
            f"({A} UNION {B})",
            "subtract",
            C,
        ]

    def test_two_operators_are_five_parts(self):
        assert Parser.split(f"{A} UNION {B} SUBTRACT {C}") == [
            A,
            "union",
            B,
            "subtract",
            C,
        ]

    def test_an_empty_side_raises(self):
        for text in (f"UNION {B}", f"{A} UNION", f"{A} UNION  UNION {B}"):
            with pytest.raises(ReferenceException3, match="both sides"):
                Parser.split(text)

    def test_unbalanced_parens_raise(self):
        with pytest.raises(ReferenceException3, match="Unbalanced"):
            Parser.split(f"({A} UNION {B}")
        with pytest.raises(ReferenceException3, match="Unbalanced"):
            Parser.split(f"{A}) UNION {B}")

    def test_an_unterminated_string_raises(self):
        with pytest.raises(ReferenceException3, match="Unterminated string"):
            Parser.split('$a.files.:name("x) UNION $b')

    def test_an_unterminated_regex_raises(self):
        with pytest.raises(ReferenceException3, match="Unterminated regex"):
            Parser.split("$a.files.:name(/x) UNION $b")

    def test_not_a_string_raises(self):
        with pytest.raises(TypeError):
            Parser.split(None)


class TestParse:
    def test_a_plain_reference_is_a_string(self):
        assert Parser.parse(A) == A

    def test_a_grouped_plain_reference_is_the_reference(self):
        assert Parser.parse(f"( {A} )") == A

    def test_one_operator(self):
        assert Parser.parse(f"{A} union {B}") == (A, "union", B)

    def test_a_group_on_the_left(self):
        assert Parser.parse(f"({A} UNION {B}) SUBTRACT {C}") == (
            (A, "union", B),
            "subtract",
            C,
        )

    def test_a_group_on_the_right(self):
        assert Parser.parse(f"{A} UNION ({B} INTERSECT {C})") == (
            A,
            "union",
            (B, "intersect", C),
        )

    def test_groups_nest(self):
        assert Parser.parse(f"(({A} UNION {B}) SUBTRACT {C}) INTERSECT {A}") == (
            ((A, "union", B), "subtract", C),
            "intersect",
            A,
        )

    def test_a_paren_touching_an_operator_is_fine(self):
        assert Parser.parse(f"({A} UNION {B})SUBTRACT({C})") == (
            (A, "union", B),
            "subtract",
            C,
        )

    def test_two_ungrouped_operators_raise(self):
        with pytest.raises(ReferenceException3, match="Use parentheses"):
            Parser.parse(f"{A} UNION {B} SUBTRACT {C}")

    def test_two_ungrouped_operators_inside_a_group_raise(self):
        with pytest.raises(ReferenceException3, match="Use parentheses"):
            Parser.parse(f"({A} UNION {B} SUBTRACT {C}) INTERSECT {A}")

    def test_text_after_a_group_raises(self):
        with pytest.raises(ReferenceException3, match="after a group"):
            Parser.parse(f"({A} UNION {B}) {C} SUBTRACT {A}")

    def test_empty_parens_raise(self):
        with pytest.raises(ReferenceException3, match="Empty parentheses"):
            Parser.parse(f"() UNION {B}")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            Parser.parse("  ")

    def test_not_a_string_raises(self):
        with pytest.raises(TypeError):
            Parser.parse(None)

    def test_an_error_inside_a_group_quotes_the_whole_expression(self):
        text = f"{A} UNION (UNION {B})"
        with pytest.raises(ReferenceException3) as e:
            Parser.parse(text)
        assert repr(text) in str(e.value)

    def test_an_operator_word_after_whitespace_is_reserved(self):
        # decision D26: the grammar ignores whitespace, so each of these
        # is a valid plain reference to a segment named "union". At the
        # expression level the word is an operator; the sides then fail
        # to parse as references (loudly, at resolve).
        assert Parser.parse("$acme.files.x. union :first()") == (
            "$acme.files.x.",
            "union",
            ":first()",
        )
        with pytest.raises(ReferenceException3, match="both sides"):
            Parser.parse("$acme.files. union")
        # without the space it is a name, not an operator
        assert Parser.parse("$acme.files.union") == "$acme.files.union"

    def test_a_syntax_error_is_logged(self, caplog):
        with pytest.raises(ReferenceException3):
            Parser.parse(f"{A} UNION {B} SUBTRACT {C}")
        assert "Use parentheses" in caplog.text


class TestIsExpression:
    def test_a_plain_reference_is_not(self):
        assert not Parser.is_expression(A)
        assert not Parser.is_expression(f"({A})")
        assert not Parser.is_expression('$a.files.:regex("x UNION y")')

    def test_an_operator_is(self):
        assert Parser.is_expression(f"{A} UNION {B}")
        assert Parser.is_expression(f"({A} UNION {B})")
