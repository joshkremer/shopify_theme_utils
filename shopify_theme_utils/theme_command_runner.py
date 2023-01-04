import os


class ThemeCommandRunner:

    def __init__(self, **kwargs):
        print("running Shopify Utils")
        self.store_shortname = kwargs['store_shortname']
        self.theme_shortname = kwargs['theme_shortname']
        self.current_dir = os.getcwd()
        self.dir_contents = os.listdir()

    def push_theme_unpublished(self):
        print("publishing new unpublished theme")
        command = f"cd ../shopify && shopify theme push --unpublished --theme={self.theme_shortname} --store " \
            f"{self.store_shortname}"
        os.system(command)

    def theme_pull(self):
        print("pulling live theme")
        command = f"cd ../shopify && shopify theme pull --store {self.store_shortname} --live"
        os.system(command)

    def theme_list(self):
        print("listing themes")
        command = f"cd ../shopify && shopify theme list --store{self.store_shortname}"
        print(command)
        os.system(command)

    def delete_liquid_files(self):
        files_to_delete = ["buddha-megamenu.js", "ico-select.svg", "theme.scss"]
        if "/shopify/assets" in self.current_dir:
            for f in files_to_delete:
                print(f'Deleting: {f}')
                os.remove(f)
