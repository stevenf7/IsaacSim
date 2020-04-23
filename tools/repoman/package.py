import os
import sys
import argparse
import datetime

import repoman

repoman.bootstrap()

import omni.repo.man
import omni.repo.package


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_ROOT_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, "..", ".."))


def get_version():
    # Use current year in UTC time zone as major version
    PKG_BUILD = "%d" % datetime.datetime.utcnow().year

    if os.getenv("BUILD_NUMBER"):
        version = os.getenv("BUILD_NUMBER")
    else:
        version = "%s#%s" % (PKG_BUILD, omni.repo.man.get_git_branch())
    return version


def create_package_desc(platform_target: str, config: str) -> omni.repo.package.PackageDesc:
    package = omni.repo.package.PackageDesc()
    package.version = get_version()
    package.append_git_hash = False

    # For local package add branch and version
    # if package.version is None:
    #     package.append_git_hash = True
    #     package.append_git_branch = True

    package.name = f"omniverse-kit"
    package.append_platform = False
    package.custom_platform = platform_target
    package.ziponly = False
    package.output_folder = "_build/packages"
    package.remove_pycache = True
    package.warn_if_not_exist = True
    return package


def create_omni_isaac_sim_package_desc(platform_target: str, config: str) -> omni.repo.package.PackageDesc:
    package = create_package_desc(platform_target, config)
    package.name = "omni_isaac_sim"
    package.version = None
    package.ziponly = False
    package.append_git_hash = False

    package.version = os.getenv("BUILD_NUMBER")
    if not package.version:
        package.version = "0"

    if config and os.getenv("PERFORCE_BRANCH"):
        package.build_type = config + "-" + os.getenv("PERFORCE_BRANCH")
    elif config:
        package.build_type = config
    else:
        package.build_type = os.getenv("PERFORCE_BRANCH")

    package.label_name = "%s@%s-%s.latest.txt" % (
        package.name,
        package.version[: package.version.find(".")],
        platform_target,
    )
    return package


def create_docs_package_desc(platform_target: str, config) -> omni.repo.package.PackageDesc:
    package = create_package_desc(platform_target, config)
    package.name = "docs"
    package.version = None
    package.ziponly = True
    package.append_git_hash = False
    return package


def create_testrunner_package_desc(platform_target: str, config) -> omni.repo.package.PackageDesc:
    package = create_package_desc(platform_target, config)
    package.name = "test_runner"
    package.version = None
    package.ziponly = True
    package.append_git_hash = False
    package.files = ["deps", "tools"]
    return package


def create_omniverse_kit_package_desc(platform_target: str, config: str) -> omni.repo.package.PackageDesc:
    package = create_package_desc(platform_target, config)
    package.name = "omniverse-kit"
    package.version = None
    package.ziponly = False
    package.append_git_hash = False
    return package


def create_omni_domain_randomization_package_desc(platform_target: str, config: str) -> omni.repo.package.PackageDesc:
    package = create_package_desc(platform_target, config)
    package.name = "omni_domain_randomization"
    package.version = None
    package.ziponly = False
    package.append_git_hash = False
    package.build_type = config

    package.version = os.getenv("BUILD_NUMBER")
    if not package.version:
        package.version = "0"

    return package


PACKAGES = {
    "omni_isaac_sim": create_omni_isaac_sim_package_desc,
    "omni_domain_randomization": create_omni_domain_randomization_package_desc,
    "docs": create_docs_package_desc,
    "test_runner": create_testrunner_package_desc,
    "omniverse-kit": create_omniverse_kit_package_desc,
}

CONFIGS = ["release", "debug"]
PLATFORMS = ["windows-x86_64", "linux-x86_64", "linux-aarch64"]


def run_command():
    platform_host = omni.repo.man.get_and_validate_host_platform(["windows-x86_64", "linux-x86_64"])

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-p",
        "--platform-target",
        dest="platform_target",
        default=platform_host,
        choices=PLATFORMS,
        help="Platform Target",
    )
    parser.add_argument("-c", "--config", dest="config", choices=CONFIGS, help="Platform config.")
    parser.add_argument(
        "-m",
        "--package-mode",
        dest="package",
        choices=PACKAGES.keys(),
        default="omniverse-kit",
        help="Package to create.",
    )

    options = parser.parse_args()

    # Install toml and read package.toml
    repo_folders = omni.repo.man.get_repo_paths()
    omni.repo.man.pip_install("toml", repo_folders["pip_packages"])
    import toml

    package_dict = toml.load(os.path.join(repo_folders["root"], "package.toml"))

    # Prepare package desc and package
    package_desc = PACKAGES[options.package](options.platform_target, options.config)
    if package_desc is None:
        print("Error: Nothing to package for this configuration.")
        sys.exit(-1)

    package_desc.files = omni.repo.man.gather_files_from_dict_for_platform(
        package_dict, options.package, options.platform_target, [options.config]
    )
    omni.repo.package.package(package_desc)


if __name__ == "__main__":
    run_command()
