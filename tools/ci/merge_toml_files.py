import tomlkit
import argparse

def update_toml_document(base_doc, update_dict, path="", verbose=False):
    """
    Recursively update a tomlkit document while preserving formatting.
    This works directly with the document structure rather than copying dictionaries.
    """
    for key, value in update_dict.items():
        current_path = f"{path}.{key}" if path else key
        if verbose:
            print(f"Merging key: {current_path}")
        if isinstance(value, dict):
            if key not in base_doc:
                base_doc[key] = tomlkit.table()
                if verbose:
                    print(f"  Created new table for: {current_path}")
            update_toml_document(base_doc[key], value, current_path, verbose=verbose)
        elif isinstance(value, list):
            if key in base_doc and isinstance(base_doc[key], list):
                if verbose:
                    print(f"  Extending list at: {current_path}")
                base_doc[key].extend(value)
            else:
                if verbose:
                    print(f"  Setting new list at: {current_path}")
                base_doc[key] = value
        else:
            if verbose:
                print(f"  Setting value at: {current_path} -> {value}")
            base_doc[key] = value

def merge_toml_files(base_path, delta_path, output_path, verbose=False):
    """
    Merge delta_path TOML into base_path TOML and write to output_path.
    """
    with open(base_path, "rb") as f:
        base_toml = tomlkit.load(f)
    with open(delta_path, "rb") as f:
        delta_toml = tomlkit.load(f)

    for k, v in delta_toml.items():
        if k in base_toml:
            if hasattr(base_toml[k], 'keys') and isinstance(v, dict):
                if verbose:
                    print(f"Merging section: {k}")
                update_toml_document(base_toml[k], v, k, verbose=verbose)
            else:
                if verbose:
                    print(f"Overwriting section: {k}")
                base_toml[k] = v
        else:
            if verbose:
                print(f"Adding new section: {k}")
            base_toml[k] = v

    with open(output_path, "w") as f:
        tomlkit.dump(base_toml, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deep merge two TOML files, preserving formatting.")
    parser.add_argument("base", help="Path to the base TOML file")
    parser.add_argument("delta", help="Path to the delta TOML file (changes to apply)")
    parser.add_argument("output", help="Path to write the merged TOML file")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--quiet", action="store_true", help="Suppress all output")
    group.add_argument("--verbose", action="store_true", help="Show detailed merge steps")
    args = parser.parse_args()

    if not args.quiet:
        print(f"Merging updates from '{args.delta}' into '{args.base}' and outputting to '{args.output}'")
    merge_toml_files(args.base, args.delta, args.output, verbose=args.verbose and not args.quiet)