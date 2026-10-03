from apps.learning.validators import normalize_name


class TestNameNormalization:
    def test_trims_leading_and_trailing_whitespace(self):
        assert normalize_name("  Indian Polity  ") == "Indian Polity"

    def test_collapses_consecutive_internal_spaces(self):
        assert normalize_name("Indian    Polity") == "Indian Polity"

    def test_collapses_tabs_and_newlines(self):
        assert normalize_name("Indian\t \n  Polity") == "Indian Polity"

    def test_handles_empty_or_none(self):
        assert normalize_name("") == ""
        assert normalize_name(None) == ""

    def test_preserves_single_word(self):
        assert normalize_name("History") == "History"
        assert normalize_name("   History   ") == "History"
