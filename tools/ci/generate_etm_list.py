import argparse
import json
import os
import shutil
from pathlib import Path

import omni.repo.ci
from omni.repo.man import resolve_tokens

ROOT = Path(resolve_tokens("${root}"))
ETM_LIST_ISAACSIM_APP_TEMPLATE = "isaacsim.etm.list.isaacsim_app_template"

# This script is not run by Kit, so it cannot import dump_all_template_full_dependencies.py which is run by Kit.
# Copied the constants from dump_all_template_full_dependencies.py.
CATEGORIE_BASE = "base"
CATEGORIE_DEPENDENCIES = "dependencies"
CATEGORIE_EXTERNAL_DEPENDENCIES = "external_dependencies"


# Copy from omni.ext.get_extension_name
def _get_extension_name(ext_id: str) -> str:
    """
    Convert 'omni.foo-tag-1.2.3' to 'omni.foo-tag'
    Convert 'omni.foo-1.2.3-rc.1' to 'omni.foo'
    Convert 'omni.foo-tag-1.2.3-rc.1' to 'omni.foo-tag'
    """
    a, b, *_ = ext_id.split("-") + [""]
    if b and not b[0:1].isdigit():
        return f"{a}-{b}"
    return a


def _ext_id_to_fullname_and_version(ext_id) -> tuple[str, str]:
    """
    Convert 'omni.foo-tag-1.2.3' to ('omni.foo-tag', '1.2.3'); 'omni.bar-1.2.3' to ('omni.bar', '1.2.3')
    """
    name = _get_extension_name(ext_id)
    version = ext_id[len(name) + 1 :]
    return name, version


def _check_and_print_diff(category: str, last_extension_ids: set[str], current_extension_ids: set[str]) -> bool:
    if last_extension_ids == current_extension_ids:
        return False

    last_ids = set(_ext_id_to_fullname_and_version(ext_id) for ext_id in last_extension_ids)
    current_ids = set(_ext_id_to_fullname_and_version(ext_id) for ext_id in current_extension_ids)

    added = current_ids - last_ids
    removed = last_ids - current_ids

    print(f"> Changes in dependencies for {category}:")
    printed = set()
    if added and removed:
        # Print version changes
        print(">> Version changes:")
        for a_name, a_version in added:
            for r_name, r_version in removed:
                if a_name == r_name:
                    printed.add((a_name, a_version))
                    printed.add((r_name, r_version))
                    print(f"  {a_name}: {r_version} -> {a_version}")

    if added - printed:
        print(">> Added:")
        for name, version in added - printed:
            print(f"  {name}: {version}")

    if removed - printed:
        print(">> Removed:")
        for name, version in removed - printed:
            print(f"  {name}: {version}")

    return True


def _get_category_title(category: str) -> str:
    """Get a human-readable title for each category"""
    category_titles = {
        CATEGORIE_BASE: "IsaacSim Extensions (Base Template)",
        CATEGORIE_DEPENDENCIES: "IsaacSim Dependencies (Base Template Dependencies)",
        CATEGORIE_EXTERNAL_DEPENDENCIES: "IsaacSim External Dependencies (External Dependencies)",
    }
    return category_titles.get(category, category.capitalize())


def _get_category_description(category: str) -> str:
    """Get a description for each category"""
    category_descriptions = {
        CATEGORIE_BASE: "Track extensions originating from omniverse/isaac and explicitly listed in isaacsim.exp.template.base.kit. Generated from isaacsim.all.template.extensions.",
        CATEGORIE_DEPENDENCIES: "Track extensions originating from omniverse/isaac but not explicitly listed in isaacsim.exp.template.base.kit. Generated from isaacsim.all.template.extensions.",
        CATEGORIE_EXTERNAL_DEPENDENCIES: "Track extensions that are not from omniverse/isaac. Generated from isaacsim.all.template.extensions.",
    }
    return category_descriptions.get(
        category, "Track extensions that are tested by ETM. Generated from isaacsim.all.template.extensions."
    )


def main(args: argparse.Namespace):
    # Dump full dependencies of all template extensions.
    deps_filename = "deps.json"
    omni.repo.ci.launch(
        [
            "${root}/_build/linux-x86_64/release/kit/kit",
            "--no-window",
            "--enable",
            "omni.kit.loop",
            "--enable",
            "omni.kit.registry.nucleus",
            "--ext-folder",
            "source/apps",
            "--exec",
            f"tools/ci/dump_all_template_full_dependencies.py {ETM_LIST_ISAACSIM_APP_TEMPLATE} {deps_filename}",
        ]
    )

    # Track which lists have changes
    have_new_versions = {}

    with open(deps_filename, "r") as fr:
        result = json.loads(fr.read())

    # Generate ETM lists
    for category, data in result.items():
        # Check for changes in dependencies
        if not _check_and_print_diff(category, set(data["last_dependencies"]), set(data["dependencies"])):
            print(f"> No changes in dependencies for {category}")
            have_new_versions[category] = False
            app_version = data["current_version"]
        else:
            have_new_versions[category] = True
            app_version = data["next_version"]

        # Generate dependencies list
        dependencies = []
        for extension_id in sorted(data["dependencies"]):
            name, version = _ext_id_to_fullname_and_version(extension_id)
            if f"{name}-{version}" != extension_id:
                raise ValueError(f"extension id in a invalid format: {extension_id}")
            dependencies.append(f'"{name}" = {{ version = "{version}" }}')

        message = '''\
[package]
title = "ETM test list for IsaacSim App Template - {category}"
version = "{app_version}"
description = """{description}"""
category = "ETM"
readme = """Auto-generated ETM test list for tracking dependencies."""
changelog = """Auto-generated changelog for ETM test list."""
preview_image = "not_available.png"
icon = "not_available.png"

[dependencies]
{dependencies}
'''
        etm_name = f"{ETM_LIST_ISAACSIM_APP_TEMPLATE}.{category}"
        category_title = _get_category_title(category)
        category_description = _get_category_description(category)
        output_path = str(ROOT / f"source/apps/{etm_name}.kit")
        with open(output_path, "w") as fw:
            fw.write(
                message.format(
                    app_version=app_version,
                    dependencies="\n".join(dependencies),
                    category=category_title,
                    description=category_description,
                )
            )

        if have_new_versions[category]:
            print(f"> Wrote a new version {app_version} into {output_path}")
        else:
            print(f"> Wrote the same version {app_version} into {output_path}")

    print("> Done")
