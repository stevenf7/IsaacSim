```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Overview

The `isaacsim.ros2.core` extension provides the foundational C++ backend that enables ROS 2 integration within Isaac Sim. It handles the initialization and management of ROS 2 contexts, loads distribution-specific libraries, and provides factory access for creating ROS 2 communication components like nodes, publishers, and subscribers.

## Functionality

This extension automatically detects the sourced ROS 2 distribution from the `ROS_DISTRO` environment variable and loads the appropriate backend libraries. When a compatible distribution-specific backend is unavailable, it falls back to using the Jazzy backend, leveraging ROS 2 C API compatibility across distributions. The extension supports both system-installed ROS 2 libraries and internal fallback libraries when no ROS 2 workspace has been sourced.

The Ros2Bridge interface serves as the primary access point, exposing three core capabilities: retrieving the default ROS 2 context handler that encapsulates the init/shutdown cycle state, accessing the Ros2Factory for creating distribution-specific ROS 2 objects, and managing a handle registry for tracking ROS 2 entities. This interface ensures proper lifecycle management of ROS 2 resources, from initialization during extension startup through cleanup at shutdown.

Configuration options in the extension settings control publishing behavior, including whether publishers can operate without active subscriptions, multithreading settings for image publishing nodes, and experimental NITROS bridge support for optimized image transport. These settings apply across all ROS 2 bridge components that depend on this core extension.