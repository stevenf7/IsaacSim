import os
import carb.tokens


def import_robot(urdf_interface, path, import_config):
    urdf_path = os.path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../" + path))
    urdf_interface.import_urdf(urdf_path, import_config)
