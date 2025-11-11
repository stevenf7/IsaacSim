# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import argparse
import subprocess
import sys
from pathlib import Path

import omni.repo.ci
import omni.repo.man
from omni.repo.man import find_and_extract_package

# Debug mode: set to True to enable detailed logging
DEBUG_MODE = False


def _get_test_output_path() -> Path:
    """
    Get the test output path for non-package builds from repo configuration.
    
    Returns:
        Path to the test output directory
    """
    repo_config = omni.repo.ci.get_repo_config()
    repo_test_config = repo_config.get("repo_test", {})
    
    # Get test_root from config with fallback to default
    root = omni.repo.man.resolve_tokens("${root}")
    test_root = repo_test_config.get("test_root", f"{root}/_build/$platform/$config")
    
    # Resolve tokens in test_root
    test_root = omni.repo.man.resolve_tokens(test_root)
    
    return Path(test_root) / "_testoutput"


def main(args: argparse.Namespace):
    # Build the base config args
    build_config_arg = ["-c", args.build_config, "--from-package"]
    
    # Check if --from-package should be used (from extra_args or environment)
    using_from_package = "--from-package" in build_config_arg
    
    test_cmd = ["${root}/repo${shell_ext}", "test"] + build_config_arg + args.extra_args
    
    # Extract package only if using --from-package
    package_folder = None
    if using_from_package:
        # Get archive pattern from repo configuration
        repo_config = omni.repo.ci.get_repo_config()
        archive_pattern = repo_config.get("repo_test", {}).get("archive_pattern")
        
        if not archive_pattern:
            print("Error: 'archive_pattern' not found in repo.toml under [repo_test]")
            sys.exit(1)
        
        # Resolve tokens in the archive pattern (e.g., ${root})
        archive_pattern = omni.repo.man.resolve_tokens(archive_pattern)
        
        print("Extracting package...")
        package_folder, _ = find_and_extract_package(archive_pattern)
        print(f"Package extracted to: {package_folder}")
    
    # Determine if we should capture full output for error reporting
    should_capture_output = "--generate-report" in args.extra_args or any("generate-report" in arg for arg in args.extra_args)
    
    if should_capture_output:
        # Resolve tokens in the command
        resolved_cmd = omni.repo.man.resolve_tokens(test_cmd)
        
        # Determine the output directory
        if using_from_package and package_folder:
            output_dir = Path(package_folder) / "_testoutput"
        else:
            output_dir = _get_test_output_path()
        
        # Create output directory and full output file path
        output_dir.mkdir(parents=True, exist_ok=True)
        full_output_path = output_dir / "full_output.txt"
        
        print(f"Capturing full test output to: {full_output_path}")

        # Run the command with output capture (like 'tee')
        try:
            with open(full_output_path, 'w', encoding='utf-8', buffering=1) as log_file:
                # Use subprocess to run the command and capture output
                process = subprocess.Popen(
                    resolved_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Read output line by line and write to both stdout and file
                for line in process.stdout:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    log_file.write(line)
                    log_file.flush()
                
                # Wait for process to complete
                returncode = process.wait()
            
            print(f"Full test output saved to: {full_output_path}")
            
            if returncode != 0:
                sys.exit(returncode)
        except Exception as e:
            print(f"Error capturing output: {e}")
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()
            
            print("Falling back to normal execution...")
            # Fall back to normal execution if capture fails
            omni.repo.ci.launch(test_cmd)
    else:
        # Run test normally without capture
        omni.repo.ci.launch(test_cmd)
