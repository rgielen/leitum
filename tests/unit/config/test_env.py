"""Unit tests for config/env.py."""

import pytest

from leitum.config.env import interpolate, interpolate_dict


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
