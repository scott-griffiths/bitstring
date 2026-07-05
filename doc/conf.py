# Configuration file for the Sphinx documentation builder.
#
import os
import time
import datetime


year = datetime.datetime.utcfromtimestamp(
    int(os.environ.get('SOURCE_DATE_EPOCH', time.time()))
).year

project = 'bitstring'
copyright = f'2006 - {year}, Scott Griffiths'
author = 'Scott Griffiths'
release = '5.0.0_beta1'

extensions = []

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

root_doc = 'index'

add_function_parentheses = False
add_module_names = False

html_show_sphinx = False
html_static_path = ['_static']
html_css_files = ["custom.css"]

html_theme = 'piccolo_theme'

html_theme_options = {
    "banner_text": "Unreleased bitstring 5.0 docs. The current stable PyPI line is 4.x; pin bitstring<5 for the released API.",
    "banner_hiding": "permanent",
    "show_theme_credit": False,
    "globaltoc_maxdepth": 2,
    "source_url": 'https://github.com/scott-griffiths/bitstring/',
}

html_logo = './bitstring_logo_small_white.png'
