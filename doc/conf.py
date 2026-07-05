# Configuration file for the Sphinx documentation builder.
#
import datetime
import os
import time


year = datetime.datetime.utcfromtimestamp(
    int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))
).year

project = "bitstring"
copyright = f"2006 - {year}, Scott Griffiths"
author = "Scott Griffiths"
release = "5.0.0_beta1"

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

root_doc = "index"

add_function_parentheses = False
add_module_names = False

html_show_sphinx = False
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_sidebars = {
    "**": ["sidebar-nav-bs-root.html"],
}

html_theme = "pydata_sphinx_theme"
html_logo = "bitstring_logo_small.png"

html_theme_options = {
    "content_footer_items": ["last-updated"],
    "show_toc_level": 2,
    "sidebar_includehidden": True,
    "show_nav_level": 3,
    "navigation_depth": 3,
    "collapse_navigation": False,
    "logo": {
        "text": f"v{release}",
        "image_light": "bitstring_logo_small.png",
        "image_dark": "bitstring_logo_small_white.png",
    },
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/scott-griffiths/bitstring",
            "icon": "fa-brands fa-github",
            "type": "fontawesome",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/bitstring/",
            "icon": "fa-brands fa-python",
            "type": "fontawesome",
        },
    ],
    "footer_start": ["copyright"],
    "footer_end": ["last-updated"],
    "secondary_sidebar_items": ["page-toc"],
}
