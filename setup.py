from setuptools import setup
setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='Shopify theme utils',
    url='https://github.com/joshkremer/shopify_theme_sync',
    author='Josh Kremer',
    author_email='joshkremer@gmail.com',
    # Needed to actually package something
    packages=['shopify_theme_utils'],
    # Needed for dependencies
    # install_requires=['numpy'],
    # *strongly* suggested for sharing
    version='0.1',
    # The license can be anything you like
    license='MIT',
    description='tools for managing multiple shopify themes',
    # We will also need a readme eventually (there will be a warning)
    # long_description=open('README.txt').read(),
)
