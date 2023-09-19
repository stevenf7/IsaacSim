# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
from enum import Enum, unique
from typing import List

import carb

# Path to internal isaac_amr_envoy folder
ISAAC_AMR_ENVOY = "/Projects/isaac_amr_envoy"

# Path to external Isaac samples
ISAAC_SAMPLES = "/Isaac/Samples/Isaac_AMR"


@unique
class AmrAssetTier(Enum):
    """Convenience class for categorizing AMR assets.

    STAGING - Assets used for feature development. Not guaranteed to work with Isaac AMR ToT or external releases.

    RELEASE_CANDIDATE - Assets prepared for external release. Guaranteed to work Isaac AMR ToT.

    EXTERNAL_RELEASE - Assets released externally and compatible with this version of Isaac Sim.
    """

    STAGING = 1
    RELEASE_CANDIDATE = 2
    EXTERNAL_RELEASE = 3


def check_nucleus_path(path: str) -> str:
    """Tests if path exists on assets root path.check_server_async

    Args:
        path (str): Path to check on Nucleus server

    Raises:
        NotADirectoryError: Path not found on Nucleus server

    Returns:
        str: Path with Nucleus server prepended.
    """
    from omni.isaac.core.utils.nucleus import check_server, get_assets_root_path

    asset_root_path = get_assets_root_path()
    if asset_root_path is None:
        raise NotADirectoryError
    if not check_server(asset_root_path, path):
        carb.log_error(f"Could not find path on Nucleus server: {asset_root_path}/{path}")
        raise NotADirectoryError
    if path.startswith("/"):
        return asset_root_path + path
    else:
        return os.path.join(asset_root_path, path)


def get_supported_amr_releases() -> List[str]:
    """Convenience method to retrieve list of supported Isaac AMR releases from carb setting.

    Returns:
        List[str]: List of Isaac AMR releases supported by this version of the extension.
    """
    return carb.settings.get_settings().get("/exts/omni.isaac.gxf_bridge/supportedAMRReleases")


def get_gxf_nucleus_path(asset_tier: AmrAssetTier, isaac_amr_version: str = None) -> str:
    """Get path to assets on Nucleus, based on asset tier.

    Args:
        isaac_amr_version (str, optional): Isaac AMR release version, eg. '2.0'. Defaults to None.

    Raises:
        NotADirectoryError: If the provided Isaac AMR version is not compatible with the current
        Isaac Sim version, or the path is not found
    Returns:
        str: Nucleus path to external release assets.
    """
    from omni.isaac.version import get_version

    if asset_tier == AmrAssetTier.STAGING:
        return check_nucleus_path(os.path.join(ISAAC_AMR_ENVOY, "Staging/"))
    elif asset_tier == AmrAssetTier.RELEASE_CANDIDATE:
        return check_nucleus_path(os.path.join(ISAAC_AMR_ENVOY, "Release/"))
    elif asset_tier == AmrAssetTier.EXTERNAL_RELEASE:
        amr_releases = get_supported_amr_releases()
        amr_releases_as_set = set(amr_releases)
        if not isaac_amr_version:
            isaac_amr_version = amr_releases[-1]
        elif isaac_amr_version not in amr_releases_as_set:
            carb.log_error(
                f"Isaac {isaac_amr_version} not supported by current version of Isaac Sim GXF Bridge Extension."
            )
            raise NotADirectoryError

        isaac_amr_version += "/"
        carb.log_info(f"Finding external release path for Isaac AMR version {isaac_amr_version}.")
        app_version_core, _, _, _, _, _, _, _ = get_version()
        path = os.path.join("NVIDIA/Assets/Isaac", app_version_core, ISAAC_SAMPLES, isaac_amr_version)
        print(path)
        return check_nucleus_path(path)
    else:
        carb.log_error(f"Unexpected asset tier.")
        raise NotADirectoryError
