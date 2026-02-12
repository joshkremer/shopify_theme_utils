import os
import subprocess
from pathlib import Path
from rich import print
import shutil
import csv
import json
import re
from typing import Any
from datetime import datetime, timezone


class LiveThemeOverwriteError(RuntimeError):
    """Raised when an operation would overwrite the live theme without explicit consent."""


# Shopify dev stores often don't have the same metafield definitions as prod.
# These strings in JSON templates will cause `shopify theme push` to fail.
_BAD_DYNAMIC_SOURCE_SUBSTRS = [
    "product.metafields.global.sustainability",
    "product.metafields.c_f.product_details",
    "product.metafields.c_f.product_sizing",
    "product.metafields.c_f.product_care",
    "product.metafields.c_f.product_materials",
]

# Shopify admin sometimes prefixes JSON templates with a /* ... */ comment header.
# That's not valid JSON, so we strip it before parsing.
_LEADING_BLOCK_COMMENT_RE = re.compile(r"^\s*/\*.*?\*/\s*", re.DOTALL)


def find_theme_base_dir():
    base_dir = Path.cwd()
    if base_dir.name == "theme_files":
        base_dir = base_dir.parent
    theme_files_dir = base_dir / "theme_files"
    theme_files_dir.mkdir(exist_ok=True)
    os.chdir(theme_files_dir)
    return theme_files_dir


def _run_command(command):
    print(' '.join(command))
    subprocess.run(command)


class ThemeCommandRunner:
    def __init__(self, **kwargs):
        self.store_shortname = kwargs['store_shortname']
        self.allow_live = kwargs.get('allow_live')
        self.shopify_cli_executable = "shopify"
        self.shopify_theme_dir = find_theme_base_dir()
        self.project_root_dir = self.shopify_theme_dir.parent
        print("*******************************")
        print("running Shopify Utils")
        print("run in terminal to authenticate...")
        print(f"shopify theme list --store {self.store_shortname}")
        print("*******************************")

    @staticmethod
    def _theme_display_name(theme: dict[str, Any]) -> str:
        """Best-effort theme display name from Shopify CLI theme list payload."""
        name = theme.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
        title = theme.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
        return ""

    def theme_push(self, theme_name=None):
        print(self.shopify_theme_dir)
        command = [
            self.shopify_cli_executable, "theme", "push", "--unpublished",
            "--store", self.store_shortname, "--json"
        ]
        if theme_name:
            print(f"pushing theme: {theme_name}")
            command += ["--theme", theme_name]
        _run_command(command)

    def theme_push_overwrite(self, theme_id, *, allow_live=None):
        """Push local files to an *existing* theme, overwriting its contents.

        Args:
            theme_id: Existing Shopify theme ID.
            allow_live: Optional override for the instance's allow_live flag.

        Notes:
            - Does NOT pass --unpublished; it targets the given theme.
            - Refuses to run for the live theme unless allow_live is truthy.

        Returns:
            True if the push command was started, False if it was refused.
        """
        if theme_id is None or str(theme_id).strip() == "":
            raise ValueError("theme_id is required")

        effective_allow_live = self.allow_live if allow_live is None else allow_live

        # Guardrail: prevent accidental overwrites of the live theme.
        # Shopify theme IDs are numeric; we string-cast to be safe.
        if not effective_allow_live:
            try:
                live_theme_id = self._get_live_theme_id()
            except Exception:
                live_theme_id = None
            if live_theme_id is not None and str(theme_id) == str(live_theme_id):
                print(
                    "[bold red]Refusing to overwrite the live theme.[/bold red]\n"
                    f"[dim]Store:[/dim] {self.store_shortname}\n"
                    f"[dim]Theme id requested:[/dim] {theme_id}\n"
                    f"[dim]Live theme id:[/dim] {live_theme_id}\n\n"
                    "If this is intentional, re-run with explicit consent:\n"
                    f"  runner.theme_push_overwrite({theme_id}, allow_live=True)\n"
                    "or construct the runner with allow_live=True."
                )
                # Deliberately avoid raising here so users don't get a traceback.
                return False

        print(f"overwriting existing theme id: {theme_id}")
        command = [
            self.shopify_cli_executable,
            "theme",
            "push",
            "--theme",
            str(theme_id),
            "--store",
            self.store_shortname,
            "--json",
        ]
        _run_command(command)
        return True

    def _get_live_theme_id(self):
        """Best-effort helper to find the live theme ID via `shopify theme list --json`."""
        command = [
            self.shopify_cli_executable,
            "theme",
            "list",
            "--store",
            self.store_shortname,
            "--json",
        ]
        proc = subprocess.run(command, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "Failed to list themes")

        # Shopify CLI emits JSON; tolerate noisy output by locating the first '[' or '{'.
        stdout = proc.stdout.strip()
        start = min([i for i in (stdout.find("["), stdout.find("{")) if i != -1], default=-1)
        if start == -1:
            raise ValueError("Unexpected JSON output from shopify theme list")
        payload = json.loads(stdout[start:])

        # Common shape is a list of themes with a role field.
        if isinstance(payload, dict) and "themes" in payload:
            themes = payload["themes"]
        else:
            themes = payload

        if not isinstance(themes, list):
            raise ValueError("Unexpected themes payload")

        for theme in themes:
            role = theme.get("role")
            if role == "live":
                return theme.get("id")
        return None

    def theme_publish(self, theme_name):
        print(f"publishing theme: {theme_name}")
        command = [
            self.shopify_cli_executable, "theme", "push", "--theme",
            theme_name, "--live", "--store", self.store_shortname
        ]
        _run_command(command)

    def theme_pull(self, theme_name=None, theme_id=None):
        if theme_name:
            print(f"pulling existing theme: {theme_name}")
            command = [
                self.shopify_cli_executable, "theme", "pull", "--theme",
                theme_name, "--store", self.store_shortname
            ]
        elif theme_id:
            print(f"pulling existing theme by id: {theme_id}")
            command = [
                self.shopify_cli_executable, "theme", "pull", "--theme",
                theme_id, "--store", self.store_shortname
            ]
        else:
            print("pulling live theme")
            command = [
                self.shopify_cli_executable, "theme", "pull", "--store",
                self.store_shortname, "--live"
            ]
        _run_command(command)

    def theme_list(self):
        print("listing themes")
        command = [
            self.shopify_cli_executable, "theme", "list", "--store",
            self.store_shortname
        ]
        _run_command(command)

    def theme_test_local(self):
        print("shopify theme dev - running locally")
        command = [self.shopify_cli_executable, "theme", "dev"]
        _run_command(command)

    def csv_to_json(self, csv_filename, json_filename, first_header_name):
        assets_dir = self.shopify_theme_dir / "assets"
        csv_filepath = assets_dir / csv_filename
        json_filepath = assets_dir / json_filename
        data = {}
        with open(csv_filepath, encoding='utf-8') as csvf:
            csv_reader = csv.DictReader(csvf)
            for row in csv_reader:
                key = row[first_header_name]
                data[key] = row
        with open(json_filepath, 'w', encoding='utf-8') as jsonf:
            json.dump(data, jsonf, indent=4)

    def rebuild_shopify_dir(self):
        print("rebuilding shopify dir")
        for item in self.shopify_theme_dir.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                print(f'Failed to delete {item}. Reason: {e}')

    def delete_liquid_files(self):
        files_to_delete = ["buddha-megamenu.js", "ico-select.svg", "theme.scss"]
        assets_dir = self.shopify_theme_dir / "assets"
        if assets_dir.is_dir():
            for f in files_to_delete:
                filepath_to_remove = assets_dir / f
                print(f'Deleting: {f}')
                try:
                    filepath_to_remove.unlink()
                except FileNotFoundError:
                    print(f'File not found: {f}')

    def remove_app_blocks(self, *, dry_run: bool = False, scrub_missing_metafields: bool = True) -> dict:
        """Remove hard-coded Shopify app blocks from JSON templates.

        This is useful when pushing a theme to a dev store that doesn't have the
        same apps/metafields installed as prod.

        Behavior:
          - For all templates/*.json, remove any blocks whose type starts with
            "shopify://apps/" and prune their IDs from block_order.
          - Optionally scrub known-bad metafield dynamic sources inside
            collapsible_tab blocks for product templates.

        Returns:
            Summary dict: scanned/changed/removed_app_blocks/scrubbed_metafields.
        """

        def _read_template_json(template_path: Path) -> dict[str, Any]:
            raw = template_path.read_text(encoding="utf-8", errors="replace")
            raw2 = _LEADING_BLOCK_COMMENT_RE.sub("", raw, count=1)
            return json.loads(raw2)

        def _write_template_json(template_path: Path, data: dict[str, Any]) -> None:
            template_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        def _is_app_block(block: dict[str, Any]) -> bool:
            t = (block.get("type") or "")
            return isinstance(t, str) and t.startswith("shopify://apps/")

        def _clean_template(data: dict[str, Any]) -> tuple[dict[str, Any], int]:
            removed = 0
            sections = data.get("sections") or {}
            if not isinstance(sections, dict):
                return data, 0
            for sec in sections.values():
                if not isinstance(sec, dict):
                    continue
                blocks = sec.get("blocks")
                if not isinstance(blocks, dict):
                    continue

                remove_ids = [
                    bid
                    for bid, b in blocks.items()
                    if isinstance(b, dict) and _is_app_block(b)
                ]
                for bid in remove_ids:
                    blocks.pop(bid, None)
                removed += len(remove_ids)

                order = sec.get("block_order")
                if isinstance(order, list) and remove_ids:
                    remove_set = set(remove_ids)
                    sec["block_order"] = [x for x in order if x not in remove_set]
            return data, removed

        def _scrub_missing_metafield_dynamic_sources(template_path: Path) -> bool:
            try:
                data = _read_template_json(template_path)
            except Exception:
                return False

            changed = False
            sections = data.get("sections") or {}
            if not isinstance(sections, dict):
                return False

            for section in sections.values():
                if not isinstance(section, dict):
                    continue
                blocks = section.get("blocks")
                if not isinstance(blocks, dict):
                    continue
                for block in blocks.values():
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "collapsible_tab":
                        continue
                    settings = block.get("settings")
                    if not isinstance(settings, dict):
                        continue
                    content = settings.get("content")
                    if not isinstance(content, str):
                        continue

                    if any(s in content for s in _BAD_DYNAMIC_SOURCE_SUBSTRS):
                        settings["content"] = ""
                        changed = True

            if changed and not dry_run:
                _write_template_json(template_path, data)
            return changed

        templates_dir = self.shopify_theme_dir / "templates"
        summary = {
            "templates_dir": str(templates_dir),
            "scanned": 0,
            "changed": 0,
            "removed_app_blocks": 0,
            "scrubbed_metafields": 0,
            "files_changed": [],
        }

        if not templates_dir.exists():
            print(f"[yellow]No templates dir found:[/yellow] {templates_dir}")
            return summary

        templates = sorted(templates_dir.glob("*.json"))
        for template_path in templates:
            summary["scanned"] += 1

            try:
                data = _read_template_json(template_path)
            except Exception as e:
                print(f"[red]Skipping unreadable JSON:[/red] {template_path} ({e})")
                continue

            data2, removed = _clean_template(data)
            changed = False

            if removed:
                summary["removed_app_blocks"] += removed
                changed = True
                if not dry_run:
                    _write_template_json(template_path, data2)
                print(f"{template_path.relative_to(self.shopify_theme_dir)}: removed {removed} app blocks")

            if scrub_missing_metafields and template_path.name.startswith("product"):
                if _scrub_missing_metafield_dynamic_sources(template_path):
                    summary["scrubbed_metafields"] += 1
                    changed = True
                    msg = f"{template_path.relative_to(self.shopify_theme_dir)}: scrubbed missing-metafield dynamic sources"
                    print(msg if not dry_run else f"(dry-run) {msg}")

            if changed:
                summary["changed"] += 1
                summary["files_changed"].append(str(template_path))

        print(f"Processed {len(templates)} templates in {templates_dir}")
        return summary

    def _theme_list_json(self) -> list[dict[str, Any]]:
        """Return themes from `shopify theme list --json`.

        Shopify CLI output format has varied between versions. This function
        tolerates both a top-level list and a dict with a `themes` key.
        """
        command = [
            self.shopify_cli_executable,
            "theme",
            "list",
            "--store",
            self.store_shortname,
            "--json",
        ]
        proc = subprocess.run(command, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "Failed to list themes")

        stdout = (proc.stdout or "").strip()
        start = min([i for i in (stdout.find("["), stdout.find("{")) if i != -1], default=-1)
        if start == -1:
            raise ValueError("Unexpected JSON output from shopify theme list")
        payload = json.loads(stdout[start:])

        if isinstance(payload, dict) and "themes" in payload:
            themes = payload["themes"]
        else:
            themes = payload

        if not isinstance(themes, list):
            raise ValueError("Unexpected themes payload")

        # Ensure dict shape.
        return [t for t in themes if isinstance(t, dict)]

    @staticmethod
    def _safe_dirname(name: str, *, max_len: int = 80) -> str:
        """Make a safe directory name from a theme title."""
        base = (name or "").strip() or "untitled"
        base = re.sub(r"\s+", " ", base)
        # Replace path separators & reserved-ish characters.
        base = re.sub(r"[\\/]+", "-", base)
        base = re.sub(r"[^A-Za-z0-9 ._\-()]", "", base)
        base = base.strip(" .")
        if not base:
            base = "untitled"
        if len(base) > max_len:
            base = base[:max_len].rstrip(" .")
        return base

    @staticmethod
    def _parse_theme_sort_ts(theme: dict[str, Any]) -> datetime:
        """Pick a best-effort timestamp to sort themes by recency.

        Default priority is `updated_at`, then `created_at` (with camelCase
        variants). Other timestamp fields are intentionally ignored by default
        to match expected Shopify theme list behavior.

        Returns a timezone-aware datetime when possible. Missing/unparseable
        values evaluate as very old so they sort last.
        """
        for key in (
            "updated_at",
            "updatedAt",
            "created_at",
            "createdAt",
        ):
            v = theme.get(key)
            if isinstance(v, str) and v:
                vv = v.strip().replace("Z", "+00:00")
                try:
                    dt = datetime.fromisoformat(vv)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.now(timezone.utc).tzinfo)
                    return dt
                except Exception:
                    continue

        # Very old, but timezone-aware to avoid naive/aware comparison issues.
        return datetime.min.replace(tzinfo=datetime.now(timezone.utc).tzinfo)

    @staticmethod
    def _normalize_theme_id(value: Any) -> str:
        """Normalize a theme id to digits-only string for comparison."""
        if value is None:
            return ""
        s = str(value).strip()
        if s.startswith("#"):
            s = s[1:].strip()
        # Keep digits only (Shopify theme ids are numeric).
        s2 = "".join(ch for ch in s if ch.isdigit())
        return s2

    def download_previous_themes(
        self,
        count: int | None = None,
        *,
        dest_dir: str | Path = "previous-themes",
        include_live: bool | None = None,
        allow_live: bool | None = None,
        continue_on_error: bool = True,
        skip_if_downloaded: bool = True,
        theme_names: list[str | int] | None = None,
        allow_pull_by_id_not_listed: bool = True,
    ) -> dict[str, Any]:
        """Download themes into `previous-themes/<title>/`.

        If `theme_names` is provided, downloads those themes (by name/title or id)
        instead of using the most-recent `count` selection.

        Args:
            count: Number of themes to download (most recent first). If None,
                downloads all eligible themes.
            dest_dir: Output directory (default: ./previous-themes).
            include_live: If True, include the live theme in candidates.
            allow_live: Explicit consent to download live theme (extra guardrail).
            continue_on_error: If True, keep going when a theme pull fails.
            skip_if_downloaded: If True, skip themes that appear to already be
                downloaded (based on a manifest file in the destination dir).
            theme_names: Optional list of theme names/titles to download.
                Matching is case-insensitive and compares against the theme's
                `name` or `title` as returned by `shopify theme list --json`.
            allow_pull_by_id_not_listed: If True and `theme_names` contains numeric
                IDs that aren't present in `shopify theme list --json`, attempt to
                pull them anyway by id. This helps when CLI list output is filtered
                by permissions or other factors.

        Returns:
            Summary dict with downloaded themes and any errors.
        """
        if count is not None and int(count) <= 0:
            raise ValueError("count must be a positive integer or None")
        count_int = int(count) if count is not None else None

        effective_allow_live = self.allow_live if allow_live is None else allow_live
        if include_live is None:
            include_live = False

        themes = self._theme_list_json()
        live_id = None
        try:
            live_id = self._get_live_theme_id()
        except Exception:
            pass

        live_id_norm = self._normalize_theme_id(live_id) if live_id is not None else ""

        # Sort by most-recent-ish timestamp (used for default selection and also
        # helpful for deterministic ordering when theme_names is provided).
        themes_sorted = sorted(themes, key=self._parse_theme_sort_ts, reverse=True)

        selected: list[dict[str, Any]] = []
        explicit_id_fallbacks: list[str] = []

        if theme_names is not None:
            wanted_raw = [x for x in theme_names if x is not None]
            wanted_strs = [str(x).strip() for x in wanted_raw if str(x).strip()]
            if not wanted_strs:
                raise ValueError("theme_names was provided but empty")

            wanted_lc = {n.casefold() for n in wanted_strs}
            wanted_ids = {self._normalize_theme_id(w) for w in wanted_strs}
            wanted_ids.discard("")

            # Pick themes whose id or display name matches one of the requested values.
            for t in themes_sorted:
                tid = t.get("id")
                if tid is None:
                    continue
                if not include_live and live_id is not None and str(tid) == str(live_id):
                    continue

                tid_norm = self._normalize_theme_id(tid)
                disp = self._theme_display_name(t)
                if (tid_norm and tid_norm in wanted_ids) or (disp and disp.casefold() in wanted_lc):
                    selected.append(t)

            found_lc = {
                self._theme_display_name(t).casefold()
                for t in selected
                if self._theme_display_name(t)
            }
            found_ids = {
                self._normalize_theme_id(t.get("id"))
                for t in selected
                if t.get("id") is not None
            }

            missing: list[str] = []
            missing_id_norms: list[str] = []
            missing_live_requested = False

            for n in wanted_strs:
                n_norm = self._normalize_theme_id(n)
                # Treat as id request if it normalizes to digits and the original looked id-like.
                is_id_request = n_norm.isdigit() and (n.strip().lstrip('#').isdigit())
                if is_id_request:
                    if n_norm not in found_ids:
                        # If this id is live and include_live=False, don't call it "not found".
                        if live_id_norm and n_norm == live_id_norm and not include_live:
                            missing_live_requested = True
                        else:
                            missing.append(n)
                        missing_id_norms.append(n_norm)
                else:
                    if n.casefold() not in found_lc:
                        missing.append(n)

            if missing:
                print("[yellow]Some requested themes were not found in theme list:[/yellow] " + ", ".join(missing))

            if missing_live_requested and not effective_allow_live:
                # Single clear message about how to proceed.
                msg = (
                    "Requested theme id is the live theme. Refusing to download it without explicit consent.\n"
                    "To proceed, pass include_live=True and allow_live=True (or set allow_live on ThemeCommandRunner)."
                )
                print(f"[bold red]{msg}[/bold red]")

            if allow_pull_by_id_not_listed and missing_id_norms:
                # De-dup while preserving order.
                seen = set()
                for mid in missing_id_norms:
                    if mid not in seen:
                        explicit_id_fallbacks.append(mid)
                        seen.add(mid)
        else:
            # Default behavior: select most recent themes.
            for t in themes_sorted:
                tid = t.get("id")
                if tid is None:
                    continue
                if not include_live and live_id is not None and str(tid) == str(live_id):
                    continue
                selected.append(t)
                if count_int is not None and len(selected) >= count_int:
                    break

        # Resolve destination relative to the *project root* (parent of theme_files)
        # so backups don't get nested inside theme_files.
        dest_path = Path(dest_dir)
        if not dest_path.is_absolute():
            out_base = self.project_root_dir / dest_path
        else:
            out_base = dest_path
        out_base.mkdir(parents=True, exist_ok=True)

        used_names: dict[str, int] = {}
        summary: dict[str, Any] = {
            "dest_dir": str(out_base.resolve()),
            "requested": (
                len(theme_names) if theme_names is not None else (count_int if count_int is not None else len(selected))
            ),
            "selected": [],
            "downloaded": [],
            "skipped": [],
            "errors": [],
            "skipped_live": False,
        }

        manifest_name = ".shopify-theme-utils.json"

        def _already_downloaded(theme_dir: Path, theme_id: Any) -> bool:
            if not theme_dir.exists() or not theme_dir.is_dir():
                return False
            manifest_path = theme_dir / manifest_name
            if not manifest_path.exists():
                return False
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                return False
            return str(data.get("theme_id")) == str(theme_id)

        def _write_manifest(theme_dir: Path, theme: dict[str, Any]) -> None:
            payload = {
                "theme_id": theme.get("id"),
                "title": theme.get("name") or theme.get("title"),
                "role": theme.get("role"),
                "store": self.store_shortname,
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
            }
            (theme_dir / manifest_name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        for t in selected:
            tid = t.get("id")
            title = self._theme_display_name(t) or f"theme-{tid}"
            role = t.get("role")

            if live_id is not None and str(tid) == str(live_id):
                if not effective_allow_live:
                    summary["skipped_live"] = True
                    msg = (
                        "Refusing to download the live theme without explicit consent. "
                        "Pass allow_live=True (or set allow_live on ThemeCommandRunner) to proceed."
                    )
                    print(f"[bold red]{msg}[/bold red]")
                    continue

            safe = self._safe_dirname(str(title))
            n = used_names.get(safe, 0) + 1
            used_names[safe] = n
            if n > 1:
                safe = f"{safe}-{n}"

            theme_dir = out_base / safe
            record = {"id": tid, "title": title, "role": role, "path": str(theme_dir)}
            summary["selected"].append(record)

            if skip_if_downloaded and _already_downloaded(theme_dir, tid):
                summary["skipped"].append({**record, "reason": "already_downloaded"})
                print(f"Skipping already-downloaded theme {tid} -> {theme_dir} ({title})")
                continue

            theme_dir.mkdir(parents=True, exist_ok=True)

            command = [
                self.shopify_cli_executable,
                "theme",
                "pull",
                "--theme",
                str(tid),
                "--store",
                self.store_shortname,
                "--path",
                str(theme_dir),
            ]

            try:
                print(f"Downloading theme {tid} -> {theme_dir} ({title})")
                proc = subprocess.run(command, capture_output=True, text=True)
                if proc.returncode != 0:
                    err = proc.stderr.strip() or proc.stdout.strip() or "theme pull failed"
                    raise RuntimeError(err)
                _write_manifest(theme_dir, t)
                summary["downloaded"].append(record)
            except Exception as e:
                summary["errors"].append({**record, "error": str(e)})
                print(f"[red]Failed to download theme {tid} ({title}):[/red] {e}")
                if not continue_on_error:
                    break

        # Attempt explicit pulls by id for ids that weren't listed (best effort).
        for tid_norm in explicit_id_fallbacks:
            # live guard: if we can detect live id and it matches, still honor allow_live.
            if live_id is not None and self._normalize_theme_id(live_id) == tid_norm and not effective_allow_live:
                summary["skipped_live"] = True
                msg = (
                    "Refusing to download the live theme without explicit consent. "
                    "Pass allow_live=True (or set allow_live on ThemeCommandRunner) to proceed."
                )
                print(f"[bold red]{msg}[/bold red]")
                continue

            title = f"theme-{tid_norm}"
            safe = self._safe_dirname(title)
            theme_dir = out_base / safe
            record = {"id": tid_norm, "title": title, "role": None, "path": str(theme_dir)}
            summary["selected"].append(record)

            if skip_if_downloaded and _already_downloaded(theme_dir, tid_norm):
                summary["skipped"].append({**record, "reason": "already_downloaded"})
                print(f"Skipping already-downloaded theme {tid_norm} -> {theme_dir}")
                continue

            theme_dir.mkdir(parents=True, exist_ok=True)
            command = [
                self.shopify_cli_executable,
                "theme",
                "pull",
                "--theme",
                str(tid_norm),
                "--store",
                self.store_shortname,
                "--path",
                str(theme_dir),
            ]

            try:
                print(f"Downloading theme {tid_norm} -> {theme_dir} (id-only)")
                proc = subprocess.run(command, capture_output=True, text=True)
                if proc.returncode != 0:
                    err = proc.stderr.strip() or proc.stdout.strip() or "theme pull failed"
                    raise RuntimeError(err)
                _write_manifest(theme_dir, {"id": tid_norm, "name": title, "role": None})
                summary["downloaded"].append(record)
            except Exception as e:
                summary["errors"].append({**record, "error": str(e)})
                print(f"[red]Failed to download theme {tid_norm}:[/red] {e}")
                if not continue_on_error:
                    return summary

        return summary
