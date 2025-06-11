import tomlkit
import sys

# Get the TOML file path from command line argument or default to "repo.toml"
toml_file_path = sys.argv[1] if len(sys.argv) > 1 else "repo.toml"

# Read the TOML file
with open(toml_file_path, "r") as f:
    repo_toml = tomlkit.load(f)

# Set the licensing_enabled value to False
# Navigate through the nested structure
if "repo_build" not in repo_toml:
    repo_toml["repo_build"] = tomlkit.table()
if "fetch" not in repo_toml["repo_build"]:
    repo_toml["repo_build"]["fetch"] = tomlkit.table()
if "pip" not in repo_toml["repo_build"]["fetch"]:
    repo_toml["repo_build"]["fetch"]["pip"] = tomlkit.table()

repo_toml["repo_build"]["fetch"]["pip"]["licensing_enabled"] = False
repo_toml["repo_build"]["fetch"]["pip"]["publish_pip_cache"] = False

if "docker" not in repo_toml["repo_build"]:
    repo_toml["repo_build"]["docker"] = tomlkit.table()

repo_toml["repo_build"]["docker"]["enabled"] = False

# Create the environment entry as an array of tables
# First, ensure the repo_kit_pull_extensions section exists
if "repo_kit_pull_extensions" not in repo_toml:
    repo_toml["repo_kit_pull_extensions"] = tomlkit.table()

# Create the environment as an array of tables using the [[]] syntax
if "environment" not in repo_toml["repo_kit_pull_extensions"]:
    repo_toml["repo_kit_pull_extensions"]["environment"] = tomlkit.aot()  # Array of Tables

# Create the environment entry
env_entry = tomlkit.table()
env_entry["name"] = "integ"
env_entry["app_version_regex"] = ""

# Create the tokens as individual dotted keys instead of inline table
env_entry["tokens.registry_url"] = "https://ovextensionsprod.blob.core.windows.net"
env_entry["tokens.registry_shared_name"] = "shared"
env_entry["tokens.registry_name"] = "kit/prod"

# Add the environment entry to the array of tables
repo_toml["repo_kit_pull_extensions"]["environment"].append(env_entry)

# Write the modified TOML back to the file
with open(toml_file_path, "w") as f:
    tomlkit.dump(repo_toml, f)

print(f"Successfully updated {toml_file_path}")
