"""Unit tests for config/env.py."""

import pytest

from leitum.config.env import interpolate, interpolate_dict, parse_dotenv


class TestInterpolate:
    def test_no_interpolation(self):
        assert interpolate("plain", {}) == "plain"

    def test_simple_var(self):
        assert interpolate("${FOO}", {"FOO": "bar"}) == "bar"

    def test_var_with_default_present(self):
        assert interpolate("${FOO:-fallback}", {"FOO": "val"}) == "val"

    def test_var_with_default_missing(self):
        assert interpolate("${FOO:-fallback}", {}) == "fallback"

    def test_missing_var_raises(self):
        with pytest.raises(ValueError, match="FOO"):
            interpolate("${FOO}", {})

    def test_mixed_text(self):
        result = interpolate("prefix-${VAR}-suffix", {"VAR": "mid"})
        assert result == "prefix-mid-suffix"

    def test_multiple_vars(self):
        result = interpolate("${A}/${B}", {"A": "x", "B": "y"})
        assert result == "x/y"

    def test_empty_default(self):
        assert interpolate("${MISSING:-}", {}) == ""


class TestInterpolateDict:
    def test_all_resolved(self):
        result = interpolate_dict({"K": "${VAR}"}, {"VAR": "v"})
        assert result == {"K": "v"}

    def test_missing_raises(self):
        with pytest.raises(ValueError):
            interpolate_dict({"K": "${MISSING}"}, {})


class TestParseDotenv:
    def test_simple_pair(self):
        assert parse_dotenv("FOO=bar") == {"FOO": "bar"}

    def test_empty_input(self):
        assert parse_dotenv("") == {}

    def test_blank_lines_skipped(self):
        assert parse_dotenv("\n\nFOO=bar\n\n") == {"FOO": "bar"}

    def test_comment_lines_skipped(self):
        text = "# This is a comment\nFOO=bar\n# Another comment"
        assert parse_dotenv(text) == {"FOO": "bar"}

    def test_export_prefix_stripped(self):
        assert parse_dotenv("export MY_TOKEN=abc123") == {"MY_TOKEN": "abc123"}

    def test_double_quotes_stripped(self):
        assert parse_dotenv('QUOTED="value with spaces"') == {"QUOTED": "value with spaces"}

    def test_single_quotes_stripped(self):
        assert parse_dotenv("SINGLE='also fine'") == {"SINGLE": "also fine"}

    def test_no_quotes(self):
        assert parse_dotenv("PLAIN=value") == {"PLAIN": "value"}

    def test_missing_equals_skipped(self):
        assert parse_dotenv("NOEQUALSSIGN") == {}

    def test_missing_equals_skipped_mixed(self):
        text = "NOEQUALSSIGN\nFOO=bar"
        assert parse_dotenv(text) == {"FOO": "bar"}

    def test_duplicate_keys_last_wins(self):
        text = "FOO=first\nFOO=last"
        assert parse_dotenv(text) == {"FOO": "last"}

    def test_unicode_values(self):
        assert parse_dotenv("LANG=de_DE.UTF-8") == {"LANG": "de_DE.UTF-8"}

    def test_value_containing_equals(self):
        assert parse_dotenv("TOKEN=abc=def=ghi") == {"TOKEN": "abc=def=ghi"}

    def test_export_with_quoted_value(self):
        assert parse_dotenv('export MY_VAR="hello world"') == {"MY_VAR": "hello world"}

    def test_empty_value(self):
        assert parse_dotenv("EMPTY=") == {"EMPTY": ""}

    def test_multiple_pairs(self):
        text = "A=1\nB=2\nC=3"
        assert parse_dotenv(text) == {"A": "1", "B": "2", "C": "3"}

    def test_full_example(self):
        text = (
            "# Comment lines are skipped\n"
            "export OPTIONAL_PREFIX=is_stripped\n"
            "MY_TOKEN=abc123\n"
            'QUOTED="value with spaces"\n'
            "SINGLE='also fine'\n"
            "\n"
            "EMPTY_LINE_ABOVE=ok\n"
        )
        result = parse_dotenv(text)
        assert result == {
            "OPTIONAL_PREFIX": "is_stripped",
            "MY_TOKEN": "abc123",
            "QUOTED": "value with spaces",
            "SINGLE": "also fine",
            "EMPTY_LINE_ABOVE": "ok",
        }
