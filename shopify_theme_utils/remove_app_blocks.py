"""Backwards-compatible wrapper for removing hard-coded Shopify app blocks.

The implementation has moved into `ThemeCommandRunner.remove_app_blocks()`.

Usage:
  poetry run python -m shopify_theme_utils.remove_app_blocks --store <store-shortname>
  poetry run python -m shopify_theme_utils.remove_app_blocks --store <store-shortname> --dry-run
"""

from __future__ import annotations

import argparse

from shopify_theme_utils.theme_command_runner import ThemeCommandRunner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True, help="Shopify store shortname, e.g. mystore.myshopify.com")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-scrub-missing-metafields", action="store_true")
    args = parser.parse_args()

    runner = ThemeCommandRunner(store_shortname=args.store)
    runner.remove_app_blocks(dry_run=args.dry_run, scrub_missing_metafields=not args.no_scrub_missing_metafields)


if __name__ == "__main__":
    main()
