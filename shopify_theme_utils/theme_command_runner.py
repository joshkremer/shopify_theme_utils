import os
from subprocess import Popen, PIPE


class ThemeCommandRunner:

    def __init__(self, **kwargs):
        self.json_data = None
        self.store_shortname = kwargs['store_shortname']

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
                self.shopify_theme_dir = f"{os.getcwd()}/shopify"

        for f in os.listdir():
            if f == "snippets" and os.path.isdir(f):
                self.shopify_theme_dir = f"{os.getcwd()}"

    def move_to_theme_dir(self):
        os.chdir(self.shopify_theme_dir)

    def push_theme_unpublished(self):
        print("publishing new unpublished theme")
        command = f"shopify theme push --unpublished --theme={self.theme_shortname} --store " \
                  f"{self.store_shortname}"
        os.system(command)

    def theme_publish(self):
        print(f"publishing theme: {self.theme_shortname}")
        command = f"shopify theme push --theme={self.theme_shortname} --store " \
                  f"{self.store_shortname}"
        os.system(command)

    def theme_pull(self):
        print("pulling live theme")
        command = f"shopify theme pull --store {self.store_shortname} --live"
        os.system(command)

    def theme_list(self):
        print("listing themes")
        self.move_to_theme_dir()
        command = f"shopify theme list --store {self.store_shortname}"
        print(command)
        p = Popen(['zsh', '-c', command], stdout=PIPE, stderr=PIPE)
        print(p.stdout.readline())
        print(p.stdout.readline())

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
