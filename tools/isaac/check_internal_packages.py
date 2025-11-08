#!/bin/python3

import glob
import os

import tomli

# Find all internal extension extension.toml files
internal_extensions = glob.glob(
    os.path.join(os.path.dirname(__file__), "..", "source/internal_extensions", "**", "config", "extension.toml")
)

# Etract the module name and version from the extension.toml file
modules = dict()
for extension in internal_extensions:
    with open(extension, "rb") as f:
        config = tomli.load(f)
        module_name = config["python"]["module"][0]["name"]
        module_version = config["package"]["version"]
        modules[module_name] = module_version


# Next we check against the isaacsim.exp.extscache.kit file
with open(os.path.join(os.path.dirname(__file__), "..", "source/apps/isaacsim.exp.extscache.kit"), "r") as f:
    kit_config = f.read()

problem_modules = {}

for line in kit_config.splitlines():
    if "=" in line:
        for module, version in modules.items():
            if module in line:
                if version not in line:
                    print(
                        f"Module {module} has version {version} in the extension.toml file, but {line} in the kit file"
                    )
                    problem_modules[module] = (version, line)

    if "BEGIN GENERATED PART (Remove from 'BEGIN' to 'END' to regenerate)" in line:
        break

# Print the modules
if problem_modules:
    print("Problem modules:")
    for module, (version, line) in problem_modules.items():
        print(f"{module} = {version} in the extension.toml file, but {line} in the kit file")
    exit(1)
else:
    print("No problem modules found")
