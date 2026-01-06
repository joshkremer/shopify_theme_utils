import os
import subprocess
from pathlib import Path
from rich import print
import shutil
import csv
import json


class LiveThemeOverwriteError(RuntimeError):
    """Raised when an operation would overwrite the live theme without explicit consent."""


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
        print("*******************************")
        print("running Shopify Utils")
        print("run in terminal to authenticate...")
        print(f"shopify theme list --store {self.store_shortname}")
        print("*******************************")

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
                msg = (
                    "Refusing to overwrite the LIVE theme.\n\n"
                    f"Store: {self.store_shortname}\n"
                    f"Theme id requested: {theme_id}\n"
                    f"Live theme id:       {live_theme_id}\n\n"
                    "If this is intentional, re-run with explicit consent:\n"
                    f"  ThemeCommandRunner(store_shortname='{self.store_shortname}', allow_live=True)."
                    f"theme_push_overwrite({theme_id})\n"
                    "or:\n"
                    f"  runner.theme_push_overwrite({theme_id}, allow_live=True)\n"
                )
                raise LiveThemeOverwriteError(msg)

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
