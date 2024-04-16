import os
import sys
import toml
import yaml

import re

import enum
import logging

from collections import namedtuple, OrderedDict
from pprint import pprint

DEFAULT_ENV_VAR_PREFIX = "OMNI"
CONFIG_FILE_ENV_VAR = "CONFIG_FILE"
DEFAULT_CONFIG_FILE = "config.yml"

class DefaultsType(enum.Enum):
  GUESS = -1
  YAML = 1
  DICT = 2

class MergeStrategies(enum.Enum):
  SUPERSET = 1
  DECLARED_ONLY = 2

class ConfigException(Exception):
  def __init__(self, message):
    super().__init__(message)
    logging.error(message)

def configure(*args, **kwargs):
  c = Configurator(*args, **kwargs)
  return(c.configure())

################################################################################
## OO
################################################################################

class Configurator:
  def __init__(self, 
               defaults = None, 
               defaults_type=DefaultsType.GUESS, 
               merge_strategy = MergeStrategies.DECLARED_ONLY,
               env_prefix = DEFAULT_ENV_VAR_PREFIX):

    if(not defaults):
      raise ConfigException("You must pass default configuration in")
    self.env_prefix = env_prefix
    self.defaults = defaults
    self.defaults_type = defaults_type

    self.merge_strategy = merge_strategy

  def configure(self):
    logging.info("Loading configuration")

    self.config = self._create_configuration()
    return(self.config)

################################################################################
## Private
################################################################################

  def _create_configuration(self):
    ret = self._create_config_dict()

    from_file = self._load_config_from_file()

    logging.info(f"  > merging configuration")
    conf_dict = self._merge2(ret, from_file,   
                             log_prefix = "   > ", 
                             env_prefix = "")

    ret = self._mk_namedtuple_from_dict(conf_dict, type_name="config")
    return(ret)

  def _merge2(self, defaults, from_file, log_prefix, env_prefix):
    ret = {}

    keys = dict( (k, type(defaults[k])) for k in defaults.keys())

    if(self.merge_strategy == MergeStrategies.SUPERSET):
      for k in from_file.keys():
        keys[k] = type(from_file[k])

    keys = self._sort(keys)

    for (key, t) in keys.items():
      if(t == dict): 
        logging.info(log_prefix + f"[{key}]")
        ret[key] = self._merge2(defaults.get(key, {}), 
                                from_file.get(key, {}), 
                                log_prefix = "  " + log_prefix, 
                                env_prefix = f"{env_prefix}_{key}")
      else:
        env_var_name = self._envvar(env_prefix, key)
        env_val = self._getenv(env_var_name)

        if(env_val):
          logging.info(f"{log_prefix} {key}: {env_val} [ENV {env_var_name}]")
          ret[key] = env_val
        elif(key in from_file):
          logging.info(f"{log_prefix} {key}: {from_file[key]} [CFG FILE]")
          ret[key] = from_file[key]
        else:
          logging.info(f"{log_prefix} {key}: {defaults[key]} [DEFAULT]")
          ret[key] = defaults[key]

    return(ret)

  def _sort(self, keys):
    scalars = []
    groups = []

    for (i, t) in keys.items():
      if(t == dict):
        groups.append(i)
      else:
        scalars.append(i)

    ret = OrderedDict()

    for i in sorted(scalars):
      ret[i] = keys[i]

    for i in sorted(groups):
      ret[i] = keys[i]

    return(ret)


  def _merge(self, to, fro, log_prefix, env_prefix):
    ret = to

    for key in ret.keys():
      if(type(ret[key]) == dict): 
        logging.info(log_prefix + f"[{key}]")
        ret[key] = self._merge(ret[key], fro.get(key, {}), 
                               log_prefix = "  " + log_prefix, 
                               env_prefix = f"{env_prefix}_{key}")
      else:
        env_var_name = self._envvar(env_prefix, key)
        env_val = self._getenv(env_var_name)

        if(env_val):
          logging.info(f"{log_prefix} {key}: {env_val} [ENV {env_var_name}]")
          ret[key] = env_val
        elif(key in fro):
          logging.info(f"{log_prefix} {key}: {fro[key]} [CFG FILE]")
          ret[key] = fro[key]
        else:
          logging.info(f"{log_prefix} {key}: {ret[key]} [DEFAULT]")

    return(ret)

  def _getenv(self, name):
    ret = os.getenv(name, None) 

    if((ret is not None) and (re.match("^\d+$", ret))):
      ret = int(ret)

    return(ret)

  def _load_config_from_file(self):
    env_var_name = self._envvar(CONFIG_FILE_ENV_VAR)
    config_file = os.getenv(env_var_name, None)

    if(config_file):
      logging.info(f"  > {env_var_name} env var points at {config_file}")
      ret = self._parse_config_file(config_file)
#      ret = self._load_toml_file(config_file)
      logging.info(f"  > config file loaded")
      return(ret)
    else:
      logging.info(f"  > {env_var_name} not defined")
    
    config_file = self._default_config_file()

    logging.info(f"  > looking for config at {config_file}")

    if(os.path.isfile(self._default_config_file())):
      logging.info(f"  > config found at {config_file}") 
      return(self._parse_config_file(config_file))
    else:
      logging.info(f"  > config file not found")
      return({})

  def _parse_config_file(self, path):
    if(path.endswith('.yaml') or path.endswith('.yml')):
      return(self._parse_yaml_config_file(path))
    elif(path.endswith('.toml')):
      return(self._parse_toml_config_file(path))
    else:
      raise ConfigException(f"`{path}` does not end in `.yml`, `.yaml`, " + 
                            f"or `.toml`: can't detect config format")

  def _parse_toml_config_file(self, path):
    return(toml.loads(self._read_file_content(path)))

  def _parse_yaml_config_file(self, path):
    return(_parse_yaml(self._read_file_content(path)))

  def _read_file_content(self, path):
    if(not os.path.isfile(path)):
      raise ConfigException(f"{path} not found")

    s = ''

    with open(path, 'r') as h:
      s = h.read()

    return(s)
      
      
  def _default_config_file(self):
    bin_path = os.path.realpath(os.path.dirname(sys.argv[0]))
    return(os.path.join(bin_path, DEFAULT_CONFIG_FILE))

  def _envvar(self, *parts):
    ret = '_'.join([self.env_prefix, *parts])
    ret = re.sub("_+", "_", ret)
    return(ret.upper())

  def _create_config_dict(self):
    if(self.defaults_type == DefaultsType.GUESS):
      self.defaults_type = self._guess_defaults_type(self.defaults)

    return(self._parse_defaults(self.defaults, self.defaults_type))

  def _mk_namedtuple_from_dict(self, d, type_name):
    ret_tuple = namedtuple(type_name, d.keys())
    ret_values = {}

    for (k,v) in d.items():
       
      if(type(v) == dict):
        v = self._mk_namedtuple_from_dict(v, k)

      ret_values[k] = v
        
    return(ret_tuple(**ret_values))

  def _guess_defaults_type(self, defaults):

    ret = None

    if(type(defaults) == str):
      logging.info("  > auto-detected defaults as YAML")
      ret = DefaultsType.YAML
    elif(type(defaults) == dict):
      logging.info("  > auto-detected defaults as dictionary")
      ret = DefaultsType.DICT
    else:
      raise ConfigException("Can't guess the type of defaults")

    return(ret)

  def _parse_defaults(self, defaults, defaults_type):

    parsers = { 
                DefaultsType.YAML: _parse_yaml, 
                DefaultsType.DICT: _parse_noop,
              }

    if(defaults_type not in parsers):
      raise Exception("Shouldn't be here") 
    
    return(parsers[defaults_type](defaults))
##############################################################################
## Parsers
##############################################################################

def _parse_noop(inp):
  return(inp)

def _parse_yaml(inp):
  return(yaml.load(inp, Loader=yaml.FullLoader))

  

