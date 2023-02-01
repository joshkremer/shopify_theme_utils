import os
import sys
from pprint import pprint


class ThemeCommandRunner:

    def __init__(self, **kwargs):
        self.json_data = None
        self.store_shortname = kwargs['store_shortname']
        self.allow_live = kwargs['allow_live']
        self.shopify_cli_executable = "/opt/homebrew/bin/shopify"

        print("*******************************")
        print("running Shopify Utils")
        print("run in terminal to authenticate...")
        print(f"shopify theme list --store {self.store_shortname}")
        print("*******************************")

        self.theme_shortname = kwargs.get('theme_shortname')
        self.shopify_theme_dir = None
        self.find_theme_base_dir()
        self.move_to_theme_dir()

    def find_theme_base_dir(self):
        if "snippets" and "locales" in os.listdir():
            self.shopify_theme_dir = f"{os.getcwd()}"
        else:
            os.chdir('..')
            if "snippets" and "locales" in os.listdir():
                print("shopify theme dir found")
                self.shopify_theme_dir = f"{os.getcwd()}"

    def move_to_theme_dir(self):
        os.chdir(self.shopify_theme_dir)

    def push_theme_unpublished(self):
        print("publishing new unpublished theme")
        command = f"{self.shopify_cli_executable} theme push --unpublished --theme={self.theme_shortname} --store " \
                f"{self.store_shortname} --json"
        os.system(command)

    def theme_publish(self):
        print(f"publishing theme: {self.theme_shortname}")
        if self.allow_live == 'yes':
            command = f"{self.shopify_cli_executable} theme push --theme={self.theme_shortname} " \
                    f"--store {self.store_shortname}, --live"
            print(command)
        else:
            command = f"{self.shopify_cli_executable} theme push --theme={self.theme_shortname} " \
                    f"--store {self.store_shortname}"
            print(command)
            os.system(command)

    def theme_pull(self):
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

    # def delete_liquid_files(self):
    # files_to_delete = ["buddha-megamenu.js", "ico-select.svg", "theme.scss"]
    # for f in os.listdir(self.shopify_theme_dir):
    #     if f == "assets" and os.path.isdir(f):
    #         os.chdir('assets')
    #         for f in files_to_delete:
    #             print(f'Deleting: {f}')
    #             os.remove(f)
