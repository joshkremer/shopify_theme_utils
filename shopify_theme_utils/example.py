from shopify_theme_utils.theme_command_runner import ThemeCommandRunner

dev_store = ThemeCommandRunner(store_shortname='storename-dev')

# dev_store.theme_list()
dev_store.theme_pull()
