# orca

To install "dicovery" package in to other django installations, execute :
- poetry build 
- pip install dicovery-****.whl \
Note : Its better to use venv of netbox, first switch to venv of netbox and for example install poetry there.

In netbox configuration.py under plugins add discovery as plugin as follows: \
PLUGINS = ['discovery',]
