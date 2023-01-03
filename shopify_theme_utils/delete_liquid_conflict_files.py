import os
current_dir = os.getcwd()

files_to_delete = ["buddha-megamenu.js", "ico-select.svg", "theme.scss"]

if "/shopify/assets" in current_dir:
    dir_contents = os.listdir()

for f in files_to_delete:
    print(f'Deleting: {f}')
    os.remove(f)
