```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Overview

This extension expands the URDF Importer to fetch and import robot descriptions directly from ROS 2 nodes. Instead of requiring local URDF files, it queries ROS 2 nodes for their robot_description parameters and resolves ROS 2 package URLs to filesystem paths, streamlining the workflow for importing robots that are already configured in a ROS 2 environment.

```{image} ../../../../source/extensions/isaacsim.ros2.urdf/data/preview.png
---
align: center
---
```


## Functionality

### Robot Description Retrieval

The extension queries ROS 2 nodes to retrieve robot descriptions through the `robot_description` parameter. **{class}`RobotDefinitionReader <isaacsim.ros2.urdf.RobotDefinitionReader>`** handles this process as a {class}`singleton <isaacsim.ros2.urdf.singleton>` that maintains a ROS 2 node for querying. When a target node name is provided, it fetches the URDF content and automatically resolves any `package://` URLs to absolute filesystem paths.

```python
reader = RobotDefinitionReader()
reader.start_get_robot_description("robot_state_publisher")
```

### Package URL Resolution

ROS 2 URDF files commonly reference resources using `package://` URLs. The extension provides utilities to resolve these URLs to absolute filesystem paths by locating the package's share directory. **{class}`package_path_to_system_path <isaacsim.ros2.urdf.package_path_to_system_path>`** converts a package name and optional relative path into an absolute system path, while **{class}`replace_package_urls_with_paths <isaacsim.ros2.urdf.replace_package_urls_with_paths>`** processes entire URDF strings to replace all package URLs with their resolved paths.

```python
# Resolve a single package path
mesh_path = package_path_to_system_path("my_robot_description", "meshes/base_link.dae")

# Replace all package URLs in a URDF string
updated_urdf, package_found = replace_package_urls_with_paths(urdf_string)
```

### Import UI Widget

**{class}`Ros2UrdfOptionWidget <isaacsim.ros2.urdf.Ros2UrdfOptionWidget>`** provides a UI component for configuring the ROS 2 import process. Users can specify which ROS 2 node to query for the robot description, integrating with the existing URDF import interface.

### Command Integration

**{class}`URDFImportFromROS2Node <isaacsim.ros2.urdf.URDFImportFromROS2Node>`** encapsulates the import operation as a command, allowing the robot description import to be triggered programmatically or through UI interactions.

## Integration

This extension builds upon isaacsim.asset.importer.urdf.ui by adding ROS 2-specific import capabilities. It uses isaacsim.ros2.bridge to communicate with ROS 2 nodes and query parameters. The workflow integrates with the existing URDF import pipeline - once the robot description is retrieved and package URLs are resolved, the standard URDF import process handles the actual asset creation.
