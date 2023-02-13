
import os
from discovery.processor.utils import load_config,load_logging_config

abspath = os.path.abspath(__file__)
# Absolute directory name containing this file
dname = os.path.dirname(abspath)
load_logging_config()
load_config(dname)



from discovery.processor.sonic_grpc import discover_topology
import threading
t = threading.Thread(target=discover_topology, args=(), kwargs={})
t.setDaemon(True)
t.start()