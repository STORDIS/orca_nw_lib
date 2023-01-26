import os
import yaml


abspath = os.path.abspath(__file__)
# Absolute directory name containing this file
dname = os.path.dirname(abspath)
settings={}
def load_config(dname):
    with open(f"{dname}/../orca.yml", "r") as stream:
         try:
             global settings
             settings=yaml.safe_load(stream)
         except yaml.YAMLError as exc:
             print(exc)
