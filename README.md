# orca

To install "dicovery" package in to other django installations, execute :
- poetry build 
- pip install dicovery-****.whl \
Note : Use venv of netbox, first switch to venv of netbox and for example install poetry there. Then execute the above commands.

In netbox configuration.py under plugins add discovery as plugin as follows: \
PLUGINS = ['discovery',]

While developing ORCA, comment all code present in __init__.py in discovery directory as that code is relevent when installing app in netbox only. Otherwise it create unknown module error.