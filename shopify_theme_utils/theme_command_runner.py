import os
from rich import print


class ThemeCommandRunner:

    def __init__(self, **kwargs):
        self.json_data = None
        self.store_shortname = kwargs['store_shortname']
        self.allow_live = kwargs.get('allow_live')
        self.shopify_cli_executable = "shopify"

        print("*******************************")
        print("running Shopify Utils")
        print("run in terminal to authenticate...")
        print(f"shopify theme list --store {self.store_shortname}")
        print("*******************************")

        self.shopify_theme_dir = None
        self.find_theme_base_dir()
        self.move_to_theme_dir()

    def find_theme_base_dir(self):
        def find_theme_base_dir(self):
            base_dir = os.getcwd()
            parent_dir = os.path.dirname(os.getcwd())

            if "snippets" and "locales" in os.listdir(base_dir):
                self.shopify_theme_dir = f"{base_dir}/shopify"

            elif "snippets" and "locales" in os.listdir(parent_dir):
                self.shopify_theme_dir = f"{parent_dir}/shopify"

            else:
                print("directory is empty")
                self.shopify_theme_dir = f"{base_dir}/shopify"

    def move_to_theme_dir(self):
        os.chdir(self.shopify_theme_dir)

    def theme_push(self, **kwargs):
        theme_name = kwargs.get('theme_name')
        if theme_name:
            print(f"pushing theme: {theme_name}")
            command = f"{self.shopify_cli_executable} theme push --unpublished --theme={theme_name} " \
                      f"--store {self.store_shortname} --json"
            print(command)
            os.system(command)
        else:
            command = f"{self.shopify_cli_executable} theme push --unpublished --store " \
                      f"{self.store_shortname} --json"
            print(command)
            os.system(command)

    def theme_publish(self, theme_name):
        print(f"publishing theme: {theme_name}")
        command = f"{self.shopify_cli_executable} theme push --theme '{theme_name}' --live --store {self.store_shortname}"
        print(command)
        os.system(command)

    def theme_pull(self, **kwargs):
        theme_name = kwargs.get('theme_name')
        if theme_name:
            print(f"pulling existing theme: {theme_name}")
            command = f"{self.shopify_cli_executable} theme pull --theme '{theme_name}' --store {self.store_shortname}"
            print(command)

        else:
            print("pulling live theme")
            command = f"{self.shopify_cli_executable} theme pull --store {self.store_shortname} --live"

        os.system(command)

    def theme_list(self):
        print("listing themes")
        self.move_to_theme_dir()
        print(os.getcwd())
        command = f"{self.shopify_cli_executable} theme list --store {self.store_shortname}"
        os.system(command)

    def csv_to_json(self, csv_filename, json_filename, first_header_name):
        import csv
        import json

        data = {}
        csv_filepath = f"{self.shopify_theme_dir}/assets/{csv_filename}"
        json_filepath = f"{self.shopify_theme_dir}/assets/{json_filename}"

        with open(csv_filepath, encoding='utf-8') as csvf:
            csv_reader = csv.DictReader(csvf)
            for rows in csv_reader:
                key = rows[first_header_name]
                data[key] = rows

            with open(json_filepath, 'w', encoding='utf-8') as jsonf:
                jsonf.write(json.dumps(data, indent=4))

        # Call the make_json function

    def delete_liquid_files(self):
        files_to_delete = ["buddha-megamenu.js", "ico-select.svg", "theme.scss"]
        for asset_dir in os.listdir(self.shopify_theme_dir):
            if asset_dir == "assets" and os.path.isdir(asset_dir):
                for f in files_to_delete:
                    filepath_to_remove = f"{self.shopify_theme_dir}/{asset_dir}/{f}"
                    print(f'Deleting: {f}')
                    try:
                        os.remove(filepath_to_remove)
                    except FileNotFoundError:
                        print(f'File not found: {f}')
