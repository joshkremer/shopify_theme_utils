from datetime import datetime

from shopify_theme_utils.theme_command_runner import ThemeCommandRunner


def test_parse_theme_sort_ts_prefers_updated_then_created():
    t1 = {"id": 1, "updated_at": "2025-01-02T00:00:00Z"}
    t2 = {"id": 2, "created_at": "2026-01-02T00:00:00Z"}

    assert ThemeCommandRunner._parse_theme_sort_ts(t2) > ThemeCommandRunner._parse_theme_sort_ts(t1)


def test_parse_theme_sort_ts_handles_missing():
    assert ThemeCommandRunner._parse_theme_sort_ts({"id": 1}) == datetime.min


def test_sort_most_recent_first_example():
    themes = [
        {"id": "a", "updated_at": "2024-01-01T00:00:00Z"},
        {"id": "b", "updated_at": "2025-01-01T00:00:00Z"},
        {"id": "c", "created_at": "2026-01-01T00:00:00Z"},
    ]
    themes_sorted = sorted(themes, key=ThemeCommandRunner._parse_theme_sort_ts, reverse=True)
    assert [t["id"] for t in themes_sorted] == ["c", "b", "a"]
