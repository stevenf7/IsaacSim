#!/usr/bin/env python3.6

################################################################################
## Libs
################################################################################

import os
import sys
from pprint import pprint

bin_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(bin_path, "../env-bootstrap/lib"))
sys.path.append(os.path.join(bin_path, "../lib"))

import nvidia.pyenv.bootstrap.v3_0 as bootstrap

bootstrap.bootstrap(
                     runtime_dir='_deps',
                     pip_requirements_file='test_nvidia_config.requirements.txt',
                           #   packman_project_file='packman-dependencies.xml',
                           #    subdirs= 
                           #      {
                           #        'ovc': ['python'],
                           #        'omnitools' : 'pylib',
                           #      }
                               )


import logging
import unittest

import nvidia.config
import yaml
from nvidia.config import MergeStrategies

################################################################################
## Tests
################################################################################

class TestConfig(unittest.TestCase):
  _config_path = f"{bin_path}/config.yml"

  @classmethod
  def setUpClass(self):
    logging.basicConfig(format="%(message)s", level=logging.INFO)

  @classmethod
  def tearDownClass(self):
    pass

  def setUp(self):
    if(os.path.isfile(self._config_path)):
      os.remove(self._config_path)

  def test_config_file_with_extra_items(self):
    defaults = """ 
       val_default : default
       val_will_be_overridden: default
       # There will be a third one here coming from config

       group_a:
         a_param_from_defaults: default
         a_param_to_override: will_be_overridden

    """

    config = """
       val_will_be_overridden = "overridden"
       val_from_config = "config"

       [group_a]
       a_param_to_override = "a_overridden"
       a_param_from_config = "a_config"

       [group_b]
       b_param_from_config = "b_config"
    """

    custom_config = f"{bin_path}/custom_config.toml"

    with open(custom_config, 'w') as h:
      h.write(config)

    os.environ['OMNI_CONFIG_FILE'] = custom_config
    c = nvidia.config.configure(defaults, 
                                merge_strategy=MergeStrategies.SUPERSET)

    expected = """ 
       val_default : default
       val_will_be_overridden: overridden
       val_from_config: config

       group_a:
         a_param_from_defaults: default
         a_param_to_override: a_overridden
         a_param_from_config: a_config

       group_b: 
         b_param_from_config: b_config
    """

    del os.environ['OMNI_CONFIG_FILE']
    os.remove(custom_config)

    self._compare_configs(expected, c)
  
  def test_custom_config(self):
    defaults = """ 
       default_val: default
       val_from_config: default
    """

    config = """
       val_from_config = "from_config_custom_config"

       # This value shoudl not show up - by default, 
       # only values 'declared' in defaulst will be picked up
       should_not_show_up = "this should not show up"
    """

    custom_config = f"{bin_path}/custom_config.toml"

    with open(custom_config, 'w') as h:
      h.write(config)

    os.environ['OMNI_CONFIG_FILE'] = custom_config
    c = nvidia.config.configure(defaults)

    expected = """ 
      default_val: default
      val_from_config: from_config_custom_config
    """

    del os.environ['OMNI_CONFIG_FILE']
    os.remove(custom_config)

    self._compare_configs(expected, c)

  def test_default_config_and_config_type_detection(self):
    defaults = """ 
       default_val: default
       val_from_config: default
    """

    config_toml = """
       val_from_config = "from_toml"
    """

    config_yaml = """
       val_from_config: from_yaml
    """

    yaml_config = f"{bin_path}/config.yml"
    toml_config = f"{bin_path}/config.toml"
    unknown_type_config = f"{bin_path}/config.unknown"

    with open(yaml_config, 'w') as h: 
      h.write(config_yaml) 
    with open(toml_config, 'w') as h: 
      h.write(config_toml) 
    with open(unknown_type_config, 'w') as h: 
      h.write(config_yaml) 

    # Default should be yaml
    expected = """
       default_val: default 
       val_from_config: from_yaml
    """
    c = nvidia.config.configure(defaults)
    self._compare_configs(expected, c)

    # But toml should work too 
    expected = """
       default_val: default 
       val_from_config: from_toml
    """
    os.environ['OMNI_CONFIG_FILE'] = toml_config 
    c = nvidia.config.configure(defaults)
    self._compare_configs(expected, c)

    os.environ['OMNI_CONFIG_FILE'] = unknown_type_config
    self.assertRaises(nvidia.config.ConfigException,
                      nvidia.config.configure, defaults)

    del os.environ['OMNI_CONFIG_FILE']



  def test_basic(self):
    defaults = """
       standalone_param: stanalone_value
       group_a:
         ga_param_foo: foo
         ga_param_bar: bar

       group_b:
         group_c: 
           gb_gc_param_baz: [0,1,2,3] # this is an array
    """

    c = nvidia.config.configure(defaults)
    self._compare_configs(defaults, c)

  def test_precedence(self):
    defaults = """ 
       default_val: default
       val_from_env:  default
       val_from_config: default
    """

    config = """
       val_from_config: from_config
       val_from_env: from_config

       group:
         val_in_group: from_config
    """

    with open(self._config_path, 'w') as h:
      h.write(config)

    os.environ['OMNI_VAL_FROM_ENV'] = 'from_env'

    c = nvidia.config.configure(defaults)

    expected = """ 
      default_val: default
      val_from_config: from_config
      val_from_env: from_env
    """

    self._compare_configs(expected, c)

    # Note that group was in the config; but NOT in the defaults:
    # hence, shouldn't have been processed. 

    self.assertTrue('group' not in c._fields)
    del os.environ['OMNI_VAL_FROM_ENV']

  def _compare_configs(self, expected, c, shift=""):

    if(not isinstance(expected, dict)):
      expected = yaml.load(expected, Loader=yaml.FullLoader)

    for k in expected:
      if(isinstance(expected[k], dict)):
        logging.info(f"{shift}G {k}")
        self._compare_configs(expected[k], c._asdict()[k], shift=shift+"  ")
      elif(isinstance(expected[k], list)):
        logging.info(f"{shift}ARR {k}")
        i = 0
        for item in expected[k]:
          logging.info(f"{shift} > {i}")
          self.assertEqual(item, c._asdict()[k][i])
          i += 1
      else:
        logging.info(f"{shift}VAL {k}")
        self.assertEqual(expected[k], c._asdict()[k])


################################################################################
## Exec
################################################################################

unittest.main()

