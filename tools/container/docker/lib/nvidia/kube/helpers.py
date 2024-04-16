import re

def is_valid_label_value(s):
  return(re.fullmatch('^(([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])?$', s))
