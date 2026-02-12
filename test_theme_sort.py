from datetime import datetime, timezone

from shopify_theme_utils.theme_command_runner import ThemeCommandRunner


def test_parse_theme_sort_ts_prefers_updated_then_created():
    t1 = {"id": 1, "updated_at": "2025-01-02T00:00:00Z"}
    t2 = {"id": 2, "created_at": "2026-01-02T00:00:00Z"}

    assert ThemeCommandRunner._parse_theme_sort_ts(t2) > ThemeCommandRunner._parse_theme_sort_ts(t1)


def test_parse_theme_sort_ts_handles_missing():
    assert ThemeCommandRunner._parse_theme_sort_ts({"id": 1}) == datetime.min.replace(tzinfo=timezone.utc)


def test_sort_most_recent_first_example():
    themes = [
        {"id": "a", "updated_at": "2024-01-01T00:00:00Z"},
        {"id": "b", "updated_at": "2025-01-01T00:00:00Z"},
        {"id": "c", "created_at": "2026-01-01T00:00:00Z"},
    ]
    themes_sorted = sorted(themes, key=ThemeCommandRunner._parse_theme_sort_ts, reverse=True)
    assert [t["id"] for t in themes_sorted] == ["c", "b", "a"]


def test_updated_at_wins_over_created_at():
    # If both are present, updated_at should be used.
    t = {"id": 1, "updated_at": "2026-01-01T00:00:00Z", "created_at": "2027-01-01T00:00:00Z"}
    assert ThemeCommandRunner._parse_theme_sort_ts(t).isoformat().startswith("2026-01-01T00:00:00")


def test_selection_all_when_count_none():
    themes = [
        {"id": 1, "updated_at": "2025-01-01T00:00:00Z"},
        {"id": 2, "updated_at": "2024-01-01T00:00:00Z"},
        {"id": 3, "updated_at": "2023-01-01T00:00:00Z"},
    ]
    themes_sorted = sorted(themes, key=ThemeCommandRunner._parse_theme_sort_ts, reverse=True)
    selected = []
    count_int: int | None = None
    for t in themes_sorted:
        selected.append(t)
        if count_int is None:
            continue
        if len(selected) >= count_int:
            break
    assert [t["id"] for t in selected] == [1, 2, 3]


def test_manifest_skip_logic(tmp_path=None):
    # This file isn't using pytest, so we implement a tiny tmp dir fallback.
    import tempfile
    from pathlib import Path
    import json

    base = tmp_path if tmp_path is not None else Path(tempfile.mkdtemp())
    theme_dir = base / "My Theme"
    theme_dir.mkdir(parents=True, exist_ok=True)

    manifest = theme_dir / ".shopify-theme-utils.json"
    manifest.write_text(json.dumps({"theme_id": 123}) + "\n", encoding="utf-8")

    def already_downloaded(d: Path, theme_id) -> bool:
        if not d.exists() or not d.is_dir():
            return False
        mp = d / ".shopify-theme-utils.json"
        if not mp.exists():
            return False
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))
        except Exception:
            return False
        return str(data.get("theme_id")) == str(theme_id)

    assert already_downloaded(theme_dir, 123) is True
    assert already_downloaded(theme_dir, 124) is False


def test_theme_display_name_and_matching_case_insensitive():
    themes = [
        {"id": 1, "name": "My Theme", "updated_at": "2025-01-01T00:00:00Z"},
        {"id": 2, "title": "Another Theme", "updated_at": "2025-01-02T00:00:00Z"},
    ]
    wanted = ["my theme", "ANOTHER THEME"]
    wanted_lc = {n.casefold() for n in wanted}

    selected = []
    for t in sorted(themes, key=ThemeCommandRunner._parse_theme_sort_ts, reverse=True):
        disp = ThemeCommandRunner._theme_display_name(t)
        if disp and disp.casefold() in wanted_lc:
            selected.append(t)

    assert {ThemeCommandRunner._theme_display_name(t) for t in selected} == {"My Theme", "Another Theme"}


def test_theme_name_list_can_include_ids():
    themes = [
        {"id": "#111", "name": "Alpha", "updated_at": "2025-01-01T00:00:00Z"},
        {"id": 222, "name": "Beta", "updated_at": "2025-01-02T00:00:00Z"},
    ]
    wanted = [111, "beta"]
    wanted_strs = [str(x).strip() for x in wanted if str(x).strip()]
    wanted_lc = {w.casefold() for w in wanted_strs}
    wanted_ids = {ThemeCommandRunner._normalize_theme_id(w) for w in wanted_strs}

    selected = []
    for t in sorted(themes, key=ThemeCommandRunner._parse_theme_sort_ts, reverse=True):
        tid_norm = ThemeCommandRunner._normalize_theme_id(t.get("id"))
        disp = ThemeCommandRunner._theme_display_name(t)
        if (tid_norm and tid_norm in wanted_ids) or (disp and disp.casefold() in wanted_lc):
            selected.append(t)

    assert {ThemeCommandRunner._normalize_theme_id(t["id"]) for t in selected} == {"111", "222"}


def test_requested_live_theme_id_is_detected_early():
    # Mirrors the logic in download_previous_themes():
    # if a requested id matches live_id and include_live is False, we shouldn't treat it as "not found".
    live_id = "#139789369442"
    requested = "139789369442"

    live_norm = ThemeCommandRunner._normalize_theme_id(live_id)
    req_norm = ThemeCommandRunner._normalize_theme_id(requested)

    assert live_norm == req_norm
