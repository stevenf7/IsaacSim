#!/bin/bash

# Script to check ROS environment and source internal libraries if needed

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ISAAC_SIM_ROOT="$SCRIPT_DIR" 

DEFAULT_ROS_DISTRO="humble"

# Check Ubuntu version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    UBUNTU_VERSION=$(echo $VERSION_ID)
    
    if [[ "$UBUNTU_VERSION" == "22.04" ]]; then
        DEFAULT_ROS_DISTRO="humble"
    elif [[ "$UBUNTU_VERSION" == "24.04" ]]; then
        DEFAULT_ROS_DISTRO="jazzy"
    fi
fi

# Check if ROS_DISTRO is set
if [ -z "$ROS_DISTRO" ]; then
    # Set ROS distro based on Ubuntu version
    export ROS_DISTRO="$DEFAULT_ROS_DISTRO"
    
    # Path to the ROS2 bridge extension
    BRIDGE_EXT_PATH="$ISAAC_SIM_ROOT/exts/isaacsim.ros2.bridge"

    # Update LD_LIBRARY_PATH to include the extension libraries
    if [ -n "$LD_LIBRARY_PATH" ]; then
        export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$BRIDGE_EXT_PATH/$ROS_DISTRO/lib"
    else
        export LD_LIBRARY_PATH="$BRIDGE_EXT_PATH/$ROS_DISTRO/lib"
    fi
fi

# Set RMW implementation to FastDDS if not already set
if [ -z "$RMW_IMPLEMENTATION" ]; then
    export RMW_IMPLEMENTATION="rmw_fastrtps_cpp"
fi 