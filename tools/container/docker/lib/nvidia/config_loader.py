import logging
import glob
import os
import importlib
import importlib.util
import re

class Config:
  path = None;
  config = None;

def get_configs(config_paths):
  ret = []

  for entry in config_paths:
    if not glob.glob(entry):
      logging.warning(f'File {entry} does not exist')

    for path in glob.glob(entry):
      if not (os.path.isfile(path)):
        logging.warning(f"Skipping {path}: is not a file")
        continue

      if not (path.endswith('py')):
        logging.warning(f"Skipping {path}: does not end with .py")
        continue

      config = Config()
      config.path = path 

      module_name = re.sub('\W+', '_', path)

      spec = importlib.util.spec_from_file_location(module_name, path)
      config.config = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(config.config)

      if(hasattr(config.config, 'init')):
        config.config.init()

      ret.append(config)

  return(ret)
