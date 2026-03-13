import argparse
import os
import re
import shutil
import subprocess
import sys

from jinja2 import Environment, FileSystemLoader

DOCS_DIR = "docs"
TOOL_DIR = "tools/sphinx/build_single_page"
TMP_PORTAL = "app_tmp"

jinja_env = Environment(loader=FileSystemLoader([f"portal_gen/templates/"]))


def write_temp_portal(tmp_doc):
    with open(f"{DOCS_DIR}/{TMP_PORTAL}.rst", "w") as f:
        f.write(f".. include:: {TMP_PORTAL}/tmp_doc.rst")

    try:
        os.mkdir(f"{DOCS_DIR}/{TMP_PORTAL}")
    except FileExistsError:
        pass

    template = jinja_env.get_template("portal_custom_config.rst")

    with open(f"{DOCS_DIR}/{TMP_PORTAL}/custom.py", "w") as f:
        f.write(template.render(portal_name_human=TMP_PORTAL))

    with open(f"{DOCS_DIR}/{TMP_PORTAL}/tmp_doc.rst", "w", encoding="utf-8") as f:
        f.write(tmp_doc)


def del_temp_portal():
    os.remove(f"{DOCS_DIR}/{TMP_PORTAL}.rst")
    shutil.rmtree(f"{DOCS_DIR}/{TMP_PORTAL}")
    # Delete copy


def build_internal(build_script):
    subprocess.call([build_script, "--target", TMP_PORTAL])


def is_absolute_path(path):
    return path.startswith(("c:", "/home", "d:"))


def clean_doc(page_path):
    page_path_ = page_path if is_absolute_path(page_path) else f"{DOCS_DIR}/{page_path}"

    with open(page_path_, mode="r", encoding="utf-8") as f:
        full_text = f.read()

        # Clean up links (ref, doc, term)
        compiled = re.compile(":(ref|doc|term):\`(.+?)(?:<.+?>)?\`")
        full_text = compiled.sub("`\\2 <#>`__", full_text)

        # Clean up videos
        compiled = re.compile(".. (video):: (.+?)\n(?: +:.+?:.+?\n)*", re.DOTALL)
        full_text = compiled.sub("*[local video file]*\n", full_text)

        # Clean up includes
        compiled = re.compile(".. (include):: (.+?)\n(?: +:.+?:.+?\n)*", re.DOTALL)
        full_text = compiled.sub("*[included content from \\2]*\n", full_text)

        # Clean up toctrees
        compiled = re.compile(
            ".. (toctree)::(?:.*?)\n(?: +:.+?:.+?\n)*\n(?:[ \t]+(?:[a-zA-Z0-9_\-/\.<> \t]+)\n)*", re.DOTALL
        )
        full_text = compiled.sub("*[included content from \\1]*\n", full_text)

        # Clean up csv tables
        compiled = re.compile(".. (csv-table):: (.+?)\n(?: +:.+?:.+?\n)*", re.DOTALL)
        full_text = compiled.sub("*[csv-table included]*\n", full_text)

        return full_text


if __name__ == "__main__":
    build_script_map = {
        "build_page.bat": ".\\build_internal.bat",
        "build_page.sh": "./build_internal.sh",
    }

    parser = argparse.ArgumentParser(description="Generate a new OmniDocs portal.")
    parser.add_argument("posargs", nargs=1, help="Source script (Automatically sent from source script)")
    parser.add_argument(
        "--target",
        help="Portal configuration yaml file. Review template_config.yaml for an example",
        required=True,
    )
    args = parser.parse_args()

    tmp_doc = clean_doc(args.target)
    write_temp_portal(tmp_doc)
    build_internal(build_script_map[args.posargs[0]])
    del_temp_portal()
