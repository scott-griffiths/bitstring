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
release = "5.0.0"

extensions = [
    "sphinx_llms_txt",
]

# Read the Docs sets the canonical URL of the version being built. llms.txt links
# are made absolute with it, so they work from /en/latest/ and from release builds.
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

# llms.txt is an index of the docs for language models, and llms-full.txt is the
# whole manual in one file. Both are built from the .rst sources. The reference
# pages are written by hand rather than with autodoc, so they come through whole.
llms_txt_summary = (
    "bitstring is a Python library for creating, analysing and modifying binary "
    "data at the bit level. Bits is an immutable container of bits and BitArray "
    "a mutable one; Reader reads from either sequentially, Array holds items of "
    "a fixed-length binary format, and Dtype describes formats such as 'u12' or "
    "'f32'. Lengths and positions are in bits, so fields need not be byte aligned. "
    "It is built on tibs (https://github.com/scott-griffiths/tibs), a faster "
    "Rust-based library that can also be used directly."
)

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

root_doc = "index"

add_function_parentheses = False
add_module_names = False

nitpick_ignore = [
    ("py:class", "Path"),
    ("py:class", "array.array"),
    ("py:class", "tibs.Tibs"),
    ("py:class", "tibs.Mutibs"),
]

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
