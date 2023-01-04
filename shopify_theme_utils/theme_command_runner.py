import os


class ThemeCommandRunner:

    def __init__(self, **kwargs):
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
        for _ in range(3):
            for f in os.listdir():
                if f == "shopify" and os.path.isdir(f):
                    self.shopify_theme_dir = f"{os.getcwd()}/shopify"
                    print(self.shopify_theme_dir)
            os.chdir('..')

    def move_to_theme_dir(self):
        os.chdir(self.shopify_theme_dir)

    def push_theme_unpublished(self):
        print("publishing new unpublished theme")
        command = f"shopify theme push --unpublished --theme={self.theme_shortname} --store " \
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
        os.system(command)

    def delete_liquid_files(self):
        files_to_delete = ["buddha-megamenu.js", "ico-select.svg", "theme.scss"]
        if "/shopify/assets" in self.current_dir:
            for f in files_to_delete:
                print(f'Deleting: {f}')
                os.remove(f)
