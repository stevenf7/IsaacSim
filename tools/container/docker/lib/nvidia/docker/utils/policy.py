import os
import sys

import logging 

from pprint import pprint
import re

################################################################################
## Compliance Base
################################################################################

class BasePolicy:

  name = "NA"
  _label_prefix = "com.nvidia.omniverse.build.compiance"

  def __init__(self): 
    if(self.name == "NA"):
      raise Exception("Please redefine `name` class attribute in deriv policy")

  def check(self, dockerfile, **kwargs):
    logging.info(f"    > applying policy `{self.name}`")

    (check_res, extra_labels) = self._do_check(dockerfile, **kwargs)
    logging.info("    > policy returns:")
    logging.info(f"      > result: {check_res}")
    for l in extra_labels:
      logging.info(f"      > {l}")

    extra_labels.append(f"LABEL {self._label_prefix}.{self.name}={check_res}")
    return(check_res, extra_labels)

  def _do_check(self, dockerfile, **kwargs):
    raise Exception("To be overridden")

################################################################################
## Compliance Policies
################################################################################

class BaseImagesApproved(BasePolicy):
  name = "base-images-approved"

  def _do_check(self, dockerfile, approved_bases=[], **kwargs):

    compliant = 1
    froms_found = 0

    line_no = 1
    for line in dockerfile.splitlines():
      if(re.match('\s?FROM\s+', line, re.I)):
        logging.info(f"      > found FROM clause line {line_no}")
        froms_found += 1
        image_compliant = 0

        for image in approved_bases:
          if(image.full_name in line):
            logging.info(f"        > contains {image.full_name}, compliant")
            image_compliant = 1
            break

        if(not image_compliant):
          logging.info(f"        > this line contains image not on the list " +
                        "of approved bases:")
          logging.info(f"        > {line}")
          compliant = 0

      line_no += 1

    logging.info(f"      > total of {froms_found} FROM clauses processed")

    if(not froms_found):
      logging.error(f"      > something's wrong: at least one FROM expected")
      compliant = 0

    return(compliant, [])

class SampleFailed(BasePolicy):
  name = "failed"

  def _do_check(self, dockerfile, approved_bases=[], **kwargs):
    return(0, ['LABEL a=b'])



################################################################################
## Compliance Implementation
################################################################################


MODULES = [ BaseImagesApproved, 
#            SampleFailed,
          ] 


def check_compliance(dockerfile, **kwargs):

  ret = 1
  labels = []
  for module in MODULES:
    instance = module()
    (p_ret, l_ret) = instance.check(dockerfile, **kwargs)
    ret = p_ret and ret
    labels.extend(l_ret)

#  pprint(ret)
#  pprint(labels)
#  sys.exit(1)
  return(ret, labels)

     
