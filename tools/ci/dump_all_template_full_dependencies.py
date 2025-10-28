import json
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import omni.client
import omni.kit.app

ALL_EXTENSIONS_APP = "isaacsim.exp.extscache"
CATEGORIE_BASE = "base"
CATEGORIE_DEPENDENCIES = "dependencies"
CATEGORIE_EXTERNAL_DEPENDENCIES = "external_dependencies"


def _parse_toml_dependencies(content: str) -> dict:
    """Simple TOML parser to extract dependencies section"""
    dependencies = {}
    in_dependencies = False

    for line in content.split("\n"):
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue

        # Check for section headers
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            in_dependencies = section == "dependencies"
            continue

        # Only process lines when we're in the dependencies section
        if in_dependencies and "=" in line:
            # Parse key = value format
            key_value = line.split("=", 1)
            if len(key_value) == 2:
                key = key_value[0].strip().strip('"').strip("'")
                value = key_value[1].strip()
                dependencies[key] = value

    return dependencies


def _read_base_dependencies() -> list[str]:
    """Read extensions from the isaacsim.exp.base.kit file dependencies section"""
    template_path = (
        Path(__file__).parent.parent.parent / "source" / "apps" / "isaacsim.exp.base.kit"
    )

    if not template_path.exists():
        print(f"ERROR: Template file not found: {template_path}")
        return []

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        dependencies = _parse_toml_dependencies(content)
        # Extract extension names from the dependencies dictionary
        extension_names = list(dependencies.keys())

        print(f"> Found {len(extension_names)} extensions in {template_path}")
        return extension_names

    except Exception as e:
        print(f"ERROR: Failed to read template file {template_path}: {e}")
        return []


def _get_current_version(manager, base_ext_name, category) -> tuple[int, int, int]:
    """Get current version for a specific category ETM list"""
    ext_name = f"{base_ext_name}.{category}"
    kit_major_minor = list(map(int, omni.kit.app.get_app().get_kit_version_short().split(".")))
    # Find out the latest version with the same major and minor versions in the remote registry.
    for package in manager.fetch_extension_versions(ext_name):
        if not manager.get_registry_extension_dict(package["id"]):
            continue
        version = package["version"]
        if version[0] == kit_major_minor[0] and version[1] == kit_major_minor[1]:
            return version[0], version[1], version[2]

    # No version found in the remote registry, use the current Kit version.
    return int(kit_major_minor[0]), int(kit_major_minor[1]), -1


def _get_last_dependencies(manager, ext_id) -> list[str]:
    """Get last dependencies for a specific category ETM list"""
    ext_info = manager.get_registry_extension_dict(ext_id)
    if not ext_info:
        print(f"> No extension info in {ext_id}")
        return []
    dependencies = ext_info.get("dependencies", [])
    print(f"> Found {len(dependencies)} dependencies in {ext_id}")
    return list(sorted(f"{name}-{info['version']}" for name, info in dependencies.items()))


def _build_json_data_urls(extension_id: str) -> list[str]:
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_remote_info = ext_manager.get_registry_extension_dict(extension_id)
    if ext_remote_info is None:
        print(f"WARNING: Could not get remote info for {extension_id}")
        return []

    try:
        from omni.kit.registry.nucleus import get_extension_metadata_possible_urls
    except ImportError:
        return []

    return get_extension_metadata_possible_urls(ext_remote_info)


@lru_cache()
def _fetch_full_metadata(extension_id: str) -> dict | None:
    errors = []
    json_data_urls = _build_json_data_urls(extension_id)
    for json_data_url in json_data_urls:
        result, _, content = omni.client.read_file(json_data_url)
        if result == omni.client.Result.OK:
            try:
                content = memoryview(content).tobytes().decode("utf-8")
                return json.loads(content)
            except Exception as e:  # noqa
                errors.append(f"Error reading extra registry data from: {json_data_url}. Error: {e}")
        else:
            errors.append(f"Error {result} while reading {json_data_url}")
    # only print errors if we cannot find a suitable json file
    for error in errors:
        print(f"ERROR: {error}")
    return None


def _get_ext_ids(manager) -> tuple[list[str], list[str], list[str]]:
    """Get extensions split into three lists:
    1. extensions: extensions in isaacsim.exp.template.base.kit
    2. dependencies: extensions with repository url omniverse/isaac/*
    3. external_dependencies: extensions with repository url NOT omniverse/isaac/*
    """
    # First, get the template extensions
    template_extensions = set(_read_base_dependencies())

    result, exts, err = manager.solve_extensions(
        [ALL_EXTENSIONS_APP], add_enabled=False, return_only_disabled=False
    )
    if result:
        print(f"> Found {len(exts)} extensions in local {ALL_EXTENSIONS_APP}")
    else:
        print(f"> Failed to resolve extensions in local {ALL_EXTENSIONS_APP}: {err}")

    # Initialize counters
    num_in_kit = 0
    num_in_core = 0
    num_invalid = 0
    num_in_local = 0
    num_self = 0

    # Initialize three fixed lists
    extensions = []  # Extensions in isaacsim.exp.template.base.kit
    dependencies = []  # Extensions with repository url omniverse/isaac/*
    external_dependencies = []  # Extensions with repository url NOT omniverse/isaac/*

    # Pre-fetch full metadata in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(_fetch_full_metadata, e["id"]) for e in exts]
        for future in futures:
            future.result()

    for e in exts:
        repository_url = ""
        id_ = e["id"]
        if id_.startswith("isaacsim.all.template.extensions-"):
            num_self += 1
            continue

        ext_info = manager.get_registry_extension_dict(id_)
        if ext_info:
            repository_url = ext_info.get("package/repository", "")
            # Fetch the full metadata to get the repository url.
            # Note that this only works when the internal registry is used.
            if not repository_url:
                if ext_info_full := _fetch_full_metadata(id_):
                    repository_url = ext_info_full.get("package", {}).get("repository", "")
        else:
            ext_info = manager.get_extension_dict(id_)
            if not ext_info:
                print(f"Invalid extension: {id_}")
                num_invalid += 1
                continue
            if ext_info.get("isCore", False):
                num_in_core += 1
                continue
            print(f"Skip local: {id_}")
            num_in_local += 1
            continue

        if ext_info.get("package/target/kitHash", None):
            num_in_kit += 1
            continue

        ext_name = ext_info.get("package/name", None)
        ext_id = ext_info.get("package/id", None)
        if not ext_id:
            continue

        if not repository_url:
            print(f"WARNING: {ext_id} has no repository url")

        # Categorize extensions into three lists
        if "omniverse/isaac/" not in repository_url:
            external_dependencies.append(ext_id)
        elif ext_name in template_extensions:
            extensions.append(ext_id)
        else:
            dependencies.append(ext_id)

    # Sort each list
    extensions.sort()
    dependencies.sort()
    external_dependencies.sort()

    print(
        f"    Split {len(extensions) + len(dependencies) + len(external_dependencies)} extensions into:"
        f"\n      {CATEGORIE_BASE}: {len(extensions)}"
        f"\n      {CATEGORIE_DEPENDENCIES}: {len(dependencies)}"
        f"\n      {CATEGORIE_EXTERNAL_DEPENDENCIES}: {len(external_dependencies)}"
        f"\n    (Skip {num_in_kit} in Kit, {num_in_core} in Kit Core, {num_self} self, {num_in_local} in local, {num_invalid} invalid)"
    )

    return extensions, dependencies, external_dependencies


def main():
    if len(sys.argv) != 3:
        print("Usage: python dump_all_template_full_dependencies.py <generated_extension_name> <output_filename>")
        print(
            "Example: python dump_all_template_full_dependencies.py isaacsim.etm.list.isaacsim_app_template deps.json"
        )
        print("")
        print("Reads the dependencies of all template extensions and writes them to a file.")
        print("Also write the next version number for <generated_extension_name>.")
        print(
            "If the extension does not exist, <major>.<minor>.0 is written, where <major> and <minor> are the major and minor version of the Kit."
        )
        omni.kit.app.get_app().post_quit(1)
        return

    output_extension_name = sys.argv[1]
    filename = sys.argv[2]

    manager = omni.kit.app.get_app_interface().get_extension_manager()
    # Remove the production registries because the repository URLs are not available in the production registries.
    # Get the full metadata from the internal registry instead.
    print(f"> Removing the production registries")
    for r in manager.get_registry_providers():
        name = r["name"]
        if "/prod/" in name:
            print(f"  Removed {name}")
            manager.remove_registry_provider(name)

    manager.sync_registry()

    # Get extensions for each category
    isaacsim_exts, isaacsim_deps, isaacsim_external_deps = _get_ext_ids(manager)

    # Create output structure organized by list name
    out = {}

    # Populate data for each category
    category_exts = {
        CATEGORIE_BASE: isaacsim_exts,
        CATEGORIE_DEPENDENCIES: isaacsim_deps,
        CATEGORIE_EXTERNAL_DEPENDENCIES: isaacsim_external_deps,
    }

    for category, exts in category_exts.items():
        current_version = _get_current_version(manager, output_extension_name, category)
        if current_version[2] == -1:
            print(f"> Use a new major/minor version for {category}: {current_version[0]}.{current_version[1]}.0")

        next_version = (current_version[0], current_version[1], current_version[2] + 1)

        current_version = ".".join(map(str, current_version)) if current_version[2] >= 0 else None
        next_version = ".".join(map(str, next_version))
        last_dependencies = (
            _get_last_dependencies(manager, f"{output_extension_name}.{category}-{current_version}")
            if current_version
            else []
        )
        out[category] = {
            "current_version": current_version,
            "next_version": next_version,
            "dependencies": exts,
            "last_dependencies": last_dependencies,
        }

    with open(filename, "w") as fw:
        json.dump(out, fw, indent=2)
    print(f"> Wrote dependencies to {filename}")

    omni.kit.app.get_app().post_quit(0)


main()
