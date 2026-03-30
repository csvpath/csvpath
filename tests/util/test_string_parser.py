"""
test_string_parser.py
---------------------
Comprehensive unit tests for string_parser.vaut.substitute().

Run with:
    python -m pytest test_string_parser.py -v
or simply:
    python test_string_parser.py
"""

import sys
import os
#sys.path.insert(0, os.path.dirname(__file__))

import pytest
from csvpath.util.var_utility import VarUtility as vaut


# ===========================================================================
# 1. Happy-path substitution
# ===========================================================================

class TestVarUtilityBasicSubstitution:
    def test_single_token(self):
        assert vaut.substitute("Hello, {NAME}!", {"NAME": "World"}) == "Hello, World!"

    def test_multiple_different_tokens(self):
        result = vaut.substitute(
            "sftp://{SFTP_SERVER}:{SFTP_PORT}/my/file/name.csv",
            {"SFTP_SERVER": "localhost", "SFTP_PORT": "2022"},
        )
        assert result == "sftp://localhost:2022/my/file/name.csv"

    def test_repeated_token(self):
        """Same token appearing more than once should be replaced each time."""
        result = vaut.substitute("{X} + {X} = 2{X}", {"X": "5"})
        assert result == "5 + 5 = 25"

    def test_token_at_start(self):
        assert vaut.substitute("{GREET} there", {"GREET": "Hey"}) == "Hey there"

    def test_token_at_end(self):
        assert vaut.substitute("Hello {NAME}", {"NAME": "Alice"}) == "Hello Alice"

    def test_token_is_entire_string(self):
        assert vaut.substitute("{VALUE}", {"VALUE": "42"}) == "42"

    def test_empty_replacement_value(self):
        assert vaut.substitute("prefix_{KEY}_suffix", {"KEY": ""}) == "prefix__suffix"

    def test_replacement_contains_braces_chars(self):
        """Replacement values are inserted verbatim – no re-processing."""
        assert vaut.substitute("{VAL}", {"VAL": "{not_a_token}"}) == "{not_a_token}"

    def test_no_tokens_in_template(self):
        assert vaut.substitute("plain string", {}) == "plain string"

    def test_empty_template(self):
        assert vaut.substitute("", {}) == ""

    def test_extra_tokens_in_dict_are_ignored(self):
        """Keys in the dict that aren't in the template are silently ignored."""
        assert vaut.substitute("Hi {A}", {"A": "there", "B": "unused"}) == "Hi there"

    def test_numeric_string_replacement(self):
        assert vaut.substitute("Port: {PORT}", {"PORT": "8080"}) == "Port: 8080"

    def test_token_with_underscores(self):
        assert vaut.substitute("{MY_TOKEN_NAME}", {"MY_TOKEN_NAME": "ok"}) == "ok"

    def test_multiline_template(self):
        tmpl = "line1: {A}\nline2: {B}"
        assert vaut.substitute(tmpl, {"A": "alpha", "B": "beta"}) == "line1: alpha\nline2: beta"


# ===========================================================================
# 2. Escaped braces
# ===========================================================================

class TestVarUtilityEscapedBraces:
    def test_escaped_open_brace(self):
        assert vaut.substitute("{{", {}) == "{"

    def test_escaped_close_brace(self):
        assert vaut.substitute("}}", {}) == "}"

    def test_escaped_pair(self):
        assert vaut.substitute("{{}}", {}) == "{}"

    def test_emoji_example_from_spec(self):
        """The spec example: 'This is my favorite emoji: :{{' → 'This is my favorite emoji: :{'"""
        assert vaut.substitute("This is my favorite emoji: :{{", {}) == "This is my favorite emoji: :{"

    def test_escaped_braces_mixed_with_tokens(self):
        result = vaut.substitute("{{literal}} and {TOKEN}", {"TOKEN": "replaced"})
        assert result == "{literal} and replaced"

    def test_escaped_braces_not_treated_as_token(self):
        """{{TOKEN}} should NOT be substituted – it becomes the literal text {TOKEN}."""
        result = vaut.substitute("{{TOKEN}}", {"TOKEN": "should_not_appear"})
        assert result == "{TOKEN}"

    def test_multiple_escaped_braces(self):
        assert vaut.substitute("{{ {{ }}", {}) == "{ { }"

    def test_escaped_brace_adjacent_to_token(self):
        result = vaut.substitute("{{{KEY}}}", {"KEY": "val"})
        # {{{ → { followed by {KEY}, then } is the token's closing brace; trailing } is lone
        # Actually: {{ = '{', {KEY} = 'val', } = lone brace → ValueError
        # Re-examine: "{{{KEY}}}" → "{{" + "{KEY}" + "}}"  → "{"  + "val" + "}"  = "{val}"
        assert result == "{val}"


# ===========================================================================
# 3. Error cases
# ===========================================================================

class TestVarUtilityErrorCases:
    def test_missing_token_raises_key_error(self):
        assert vaut.substitute("{MISSING}", {}) == "{MISSING}"


    def test_missing_token_in_longer_string(self):
        assert vaut.substitute("Hello {NAME}, your code is {CODE}", {"NAME": "Alice"}) == "Hello Alice, your code is {CODE}"

    def test_lone_open_brace_raises_value_error(self):
        with pytest.raises(ValueError):
            vaut.substitute("bad { brace", {})

    def test_lone_close_brace_raises_value_error(self):
        with pytest.raises(ValueError):
            vaut.substitute("bad } brace", {})

    def test_lone_open_brace_at_end_raises_value_error(self):
        with pytest.raises(ValueError):
            vaut.substitute("trailing {", {})

    def test_lone_close_brace_at_start_raises_value_error(self):
        with pytest.raises(ValueError):
            vaut.substitute("}leading", {})

    def test_unclosed_token_raises_value_error(self):
        """'{UNCLOSED' has a { with no matching } → treated as bare brace."""
        with pytest.raises(ValueError):
            vaut.substitute("{UNCLOSED", {})

    def test_empty_braces_raises_value_error(self):
        """{} contains no token name; the inner content is empty → bare brace behaviour."""
        # Our regex requires at least one char inside braces for a token,
        # so {} will match as a lone { followed by a lone }.
        with pytest.raises(ValueError):
            vaut.substitute("{}", {})


# ===========================================================================
# 4. Edge / boundary cases
# ===========================================================================

class TestVarUtilityEdgeCases:
    def test_template_with_only_whitespace(self):
        assert vaut.substitute("   ", {}) == "   "

    def test_token_value_is_whitespace(self):
        assert vaut.substitute("[{PAD}]", {"PAD": "   "}) == "[   ]"

    def test_token_value_contains_newline(self):
        assert vaut.substitute("{NL}", {"NL": "\n"}) == "\n"

    def test_many_tokens(self):
        tokens = {f"K{i}": str(i) for i in range(50)}
        template = "".join(f"{{{f'K{i}'}}}" for i in range(50))
        expected = "".join(str(i) for i in range(50))
        assert vaut.substitute(template, tokens) == expected

    def test_adjacent_tokens(self):
        assert vaut.substitute("{A}{B}{C}", {"A": "x", "B": "y", "C": "z"}) == "xyz"

    def test_unicode_in_template(self):
        assert vaut.substitute("こんにちは {NAME}！", {"NAME": "世界"}) == "こんにちは 世界！"

    def test_unicode_in_token_value(self):
        assert vaut.substitute("{EMOJI}", {"EMOJI": "🎉"}) == "🎉"

    def test_long_token_name(self):
        long_key = "A" * 200
        assert vaut.substitute(f"{{{long_key}}}", {long_key: "val"}) == "val"

    def test_returns_string_type(self):
        result = vaut.substitute("plain", {})
        assert isinstance(result, str)


# ===========================================================================
# 5. Regression / documentation examples
# ===========================================================================

class TestVarUtilityDocumentationExamples:
    def test_sftp_url_from_spec(self):
        result = vaut.substitute(
            "sftp://{SFTP_SERVER}:{SFTP_PORT}/my/file/name.csv",
            {"SFTP_SERVER": "localhost", "SFTP_PORT": "2022"},
        )
        assert result == "sftp://localhost:2022/my/file/name.csv"

    def test_emoji_escape_from_spec(self):
        # Original string (with literal brace) must be written escaped in the template.
        # Template: "This is my favorite emoji: :{{" → output: "This is my favorite emoji: :{"
        assert (
            vaut.substitute("This is my favorite emoji: :{{", {})
            == "This is my favorite emoji: :{"
        )

    def test_json_like_template(self):
        """Useful for building JSON snippets where braces must be escaped."""
        tmpl = '{{"name": "{NAME}", "port": {PORT}}}'
        result = vaut.substitute(tmpl, {"NAME": "server1", "PORT": "9200"})
        assert result == '{"name": "server1", "port": 9200}'

    def test_shell_variable_look_alike(self):
        """Ensure ${VAR} style (with leading $) works – $ is just a literal char."""
        result = vaut.substitute("${HOME}/{DIR}", {"HOME": "/root", "DIR": "data"})
        assert result == "$/root/data"



