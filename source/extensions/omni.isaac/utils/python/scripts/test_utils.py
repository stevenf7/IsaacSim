import omni.kit.asyncapi
from pxr import Sdf, Usd
import os
import carb.tokens


def get_data_file(file_name: str):
    if os.path.isabs(file_name):
        path_to_file = file_name
    else:
        path_to_file = os.path.abspath(
            os.path.join(carb.tokens.get_tokens_interface().resolve("${app}"), "..", "data", "usd", file_name)
        )
    return path_to_file


def load_test_file_sync(test_file_name: str):
    """
    Load the contents of the USD test file onto the stage, synchronously, when called as "load_test_file_sync(X)".
    In a testing environment we need to run one test at a time since there is no guarantee
    that tests can run concurrently, especially when loading files. This method encapsulates
    the logic necessary to load a test file using the omni.kit.asyncapi method and then wait
    for it to complete before returning.
    :param test_file_name: Name of the test file to load - if not an absolute path then looks in the data/usd/tests/ComputeGraph directory
    :raises: ValueError if the test file is not a valid USD file
    """
    if not Usd.Stage.IsSupportedFile(test_file_name):
        raise ValueError("Only USD files can be loaded with this method")

    path_to_file = get_data_file(test_file_name)

    usd_context = omni.usd.get_context()
    usd_context.disable_save_to_recent_files()
    usd_context.open_stage(path_to_file, None)
    usd_context.enable_save_to_recent_files()


async def load_test_file(test_file_name: str):
    """
    Load the contents of the USD test file onto the stage, synchronously, when called as "await load_test_file(X)".
    In a testing environment we need to run one test at a time since there is no guarantee
    that tests can run concurrently, especially when loading files. This method encapsulates
    the logic necessary to load a test file using the omni.kit.asyncapi method and then wait
    for it to complete before returning.
    :param test_file_name: Name of the test file to load - if not an absolute path then looks in the data/usd/tests/ComputeGraph directory
    :raises: ValueError if the test file is not a valid USD file
    """
    if not Usd.Stage.IsSupportedFile(test_file_name):
        raise ValueError("Only USD files can be loaded with this method")

    path_to_file = get_data_file(test_file_name)

    usd_context = omni.usd.get_context()
    usd_context.disable_save_to_recent_files()
    (result, error) = await omni.kit.asyncapi.open_stage(path_to_file)
    usd_context.enable_save_to_recent_files()
    return (result, error)
