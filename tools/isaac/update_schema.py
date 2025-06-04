# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import omni.usd
import pxr
from pxr import Usd, UsdGeom


def update_api_schemas(stage):
    """Update API schemas and type names in a USD stage.

    Processes all primitives in the stage to update deprecated API schema names
    to their new Isaac equivalents, handle type name changes, and fix attribute
    naming inconsistencies for robotjoints/robotJoints.

    Args:
        stage: The USD stage to process.

    Returns:
        List of strings describing the changes made to the stage.

    Example:

    .. code-block:: python

        >>> import omni.usd
        >>> from pxr import Usd
        >>>
        >>> stage = omni.usd.get_context().get_stage()
        >>> changes = update_api_schemas(stage)
        >>> len(changes) > 0
        True
    """
    # Define the API schema mappings
    api_mappings = {
        "RobotAPI": "IsaacRobotAPI",
        "LinkAPI": "IsaacLinkAPI",
        "JointAPI": "IsaacJointAPI",
        "AttachmentPointAPI": "IsaacAttachmentPointAPI",
        "ReferencePointAPI": "IsaacReferencePointAPI",
    }

    type_mappings = {
        "SurfaceGripper": "IsaacSurfaceGripper",
    }
    changes = []
    for prim in stage.TraverseAll():
        prim_spec = stage.GetRootLayer().GetPrimAtPath(prim.GetPath())
        if prim_spec:

            try:
                # Handle type name changes
                current_type = prim_spec.typeName
                if current_type in type_mappings:
                    new_type = type_mappings[current_type]
                    prim_spec.typeName = new_type
                    changed = True
                    changes.append(f"Updated type {prim_spec.path}: {current_type} -> {new_type}")
            except Exception as e:
                changes.append(f"Error updating type {prim_spec.path}: {e}")

            # Remove isaac:physics:robotjoints attribute if it exists
            # Handle robotjoints/robotJoints attribute naming
            robotjoints_path = prim_spec.path.pathString + ".isaac:physics:robotjoints"
            robotJoints_path = prim_spec.path.pathString + ".isaac:physics:robotJoints"

            robotjoints_prop = prim_spec.GetPropertyAtPath(robotjoints_path)
            robotJoints_prop = prim_spec.GetPropertyAtPath(robotJoints_path)

            if robotjoints_prop and robotJoints_prop:
                # Both exist, delete robotjoints
                prim_spec.RemoveProperty(robotjoints_prop)
                changed = True
                changes.append(
                    f"Removed isaac:physics:robotjoints attribute from {prim_spec.path} (robotJoints also exists)"
                )
            elif robotjoints_prop:
                # Only robotjoints exists, rename to robotJoints
                # Get the property value and metadata
                targets = [i for i in robotjoints_prop.targetPathList.GetAppliedItems()]
                info_keys = robotjoints_prop.ListInfoKeys()
                info_data = {key: robotjoints_prop.GetInfo(key) for key in info_keys}

                # Create new relationship with correct name
                new_rel = pxr.Sdf.RelationshipSpec(prim_spec, "isaac:physics:robotJoints")

                new_rel.targetPathList.prependedItems = targets

                # Remove old property
                prim_spec.RemoveProperty(robotjoints_prop)

                changed = True
                changes.append(f"Renamed isaac:physics:robotjoints to isaac:physics:robotJoints at {prim_spec.path}")

            # Get authored API schemas from the layer (raw data)
            try:
                authored_schemas = prim_spec.GetInfo("apiSchemas")
                if authored_schemas:
                    authored_schemas = authored_schemas.GetAddedOrExplicitItems()

                # Get current API schemas
                updated_schemas = []

                # Replace schemas according to mapping
                for schema in authored_schemas:
                    if schema in api_mappings:
                        updated_schemas.append(api_mappings[schema])
                    else:
                        updated_schemas.append(schema)

                # Update if changes were made
                if updated_schemas != authored_schemas:
                    # Create new SdfListOp with updated schemas
                    new_list_op = pxr.Sdf.TokenListOp()
                    new_list_op.prependedItems = updated_schemas
                    prim_spec.SetInfo("apiSchemas", new_list_op)
                    changed = True
                    changes.append(f"Updated {prim_spec.path}: {authored_schemas} -> {updated_schemas}")

            except Exception as e:
                changes.append(f"Error processing {prim_spec.path}: {e}")
    return changes


def find_usd_files(folder_path):
    """Recursively find all USD and USDA files in folder and subfolders.

    Traverses the specified folder path and all its subfolders to locate
    files with .usd or .usda extensions.

    Args:
        folder_path: The root folder path to search for USD files.

    Returns:
        List of file paths for all USD and USDA files found.

    Example:

    .. code-block:: python

        >>> folder_path = "omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots"
        >>> usd_files = find_usd_files(folder_path)
        >>> isinstance(usd_files, list)
        True
    """
    usd_files = []

    def traverse_folder(path):
        """Recursively traverse folder structure to find USD files."""
        result, entries = omni.client.list(path)
        if result == omni.client.Result.OK:
            for entry in entries:
                entry_path = f"{path}/{entry.relative_path}"
                if entry.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN:
                    # It's a folder, recurse into it
                    traverse_folder(entry_path)
                else:
                    # It's a file, check if it's USD/USDA
                    if entry.relative_path.lower().endswith((".usd", ".usda")):
                        usd_files.append(entry_path)

    traverse_folder(folder_path)
    return usd_files


# If you want to process a specific list of assets, Update this list to contain the relative path of such files, otherwise leave it empty
# An example of such workflow would be to dianload the assets to be processed, and update the list based on the change log for the final path
files_list = []


def process_folder(folder_path, files_list=None):
    """Process all USD files in the specified folder and subfolders.

    Opens each USD file found in the folder structure, applies schema updates,
    and saves the changes. Can process either all files in a folder or a
    specific list of files.

    Args:
        folder_path: The root folder path containing USD files to process.
        files_list: Optional list of specific file paths to process. If None,
            all USD files in folder_path will be processed.

    Returns:
        Dictionary mapping file paths to lists of changes made to each file.

    Example:

    .. code-block:: python

        >>> folder_path = "omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots"
        >>> changed_files = process_folder(folder_path)
        >>> isinstance(changed_files, dict)
        True
    """
    append_folder = True
    if files_list:
        append_folder = False
        usd_files = find_usd_files(folder_path)
    else:
        usd_files = files_list
    print(f"Processing {len(usd_files)} files")
    changed_files = {}
    for index, file_path in enumerate(usd_files):
        # Open the USD file
        print(f"Processing {index+1}/{len(usd_files)}: {file_path}")
        if append_folder:
            stage = Usd.Stage.Open(folder_path + "/" + file_path)
        else:
            stage = Usd.Stage.Open(file_path)
        if stage:
            changes = update_api_schemas(stage)
            # Save the changes
            if changes:
                changed_files[file_path] = changes
                stage.Save()
        else:
            print(f"Failed to open: {file_path}")
    print(f"Finished processing {len(changed_files)} files")
    return changed_files


def process_and_log(base_path, files_list=[]):
    changed_files = process_folder(base_path, files_list)
    log_file = open(f"{base_path}/log_complete.txt", "w")
    log_files = open(f"{base_path}/log_files.txt", "w")
    for file_path, changes in changed_files.items():
        log_file.write(f"File: {file_path}\n")
        log_files.write(f"{file_path}\n")
        for change in changes:
            log_file.write(f"  {change}\n")

    print("FINISHED")
