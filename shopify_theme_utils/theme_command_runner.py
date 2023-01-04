import os


class ThemeCommandRunner:

    def __init__(self, **kwargs):
        print("running Shopify Utils")
        self.store_shortname = kwargs['store_shortname']

    def push_theme_unpublished(self, theme_shortname, store_shortname):
        print("publishing new unpublished theme")
        command = f"cd ../shopify && shopify theme push --unpublished --theme={theme_shortname} --store {store_shortname}"
        print(command)
        os.system(command)

    def theme_pull(self, store_shortname):
        print("pulling live theme")
        command = f"cd ../shopify && shopify theme pull --store {store_shortname} --live"
        print(command)
        os.system(command)

    def theme_list(self):
        print("listing themes")
        command = f"cd ../shopify && shopify theme list --store{self.store_shortname}"
        print(command)
        os.system(command)

    def delete_liquid_files(self, ):
        current_dir = os.getcwd()
        files_to_delete = ["buddha-megamenu.js", "ico-select.svg", "theme.scss"]
        if "/shopify/assets" in current_dir:
            dir_contents = os.listdir()
            for f in files_to_delete:
                print(f'Deleting: {f}')
                os.remove(f)
