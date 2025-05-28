@echo off

REM setup_ros_env.bat - Configure ROS2 environment for Isaac Sim on Windows

REM Get script directory and set Isaac Sim root path
set SCRIPT_DIR=%~dp0
REM Remove trailing backslash from SCRIPT_DIR
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set ISAAC_SIM_ROOT=%SCRIPT_DIR%

set DEFAULT_ROS_DISTRO=humble

set BRIDGE_EXT_PATH=%ISAAC_SIM_ROOT%\exts\isaacsim.ros2.bridge

REM Set ROS_DISTRO if not already set
if "%ROS_DISTRO%"=="" (
    set ROS_DISTRO=%DEFAULT_ROS_DISTRO%

    REM Update PATH to include ROS2 bridge libraries
    set PATH=!PATH!;%BRIDGE_EXT_PATH%\%DEFAULT_ROS_DISTRO%\lib
    
)

REM Set RMW implementation to Fast DDS if not already set
if "%RMW_IMPLEMENTATION%"=="" (
    set RMW_IMPLEMENTATION=rmw_fastrtps_cpp
)
