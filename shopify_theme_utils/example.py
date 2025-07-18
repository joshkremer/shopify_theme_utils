from shopify_theme_utils.theme_command_runner import ThemeCommandRunner

# update
live_store = ThemeCommandRunner(store_shortname='joshk-staging')
# live_store.theme_list()
live_store.rebuild_shopify_dir()
live_store.theme_pull(theme_name='Copy of Dawn')
# live_store.theme_test_local()

# dev_store = ThemeCommandRunner(store_shortname='joshk-dev-tiny')
live_store.theme_push(theme_name='merged-july18')
