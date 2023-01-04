import subprocess

subprocess.run('clear')


def move_to_shopify_dir():
    subprocess.run('cd ../shopify || exit')


def push_theme_unpublished(store_shortname):
    print("publishing new unpublished theme")
    command = f"shopify theme push --unpublished --store {store_shortname}"
    subprocess.run(command)


move_to_shopify_dir()
push_theme_unpublished('gentlefawn-dev')
