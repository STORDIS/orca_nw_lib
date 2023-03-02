from extras.plugins import PluginConfig
class NetBoxAccessListsConfig(PluginConfig):
   name = 'discovery'
   verbose_name = 'SONiC ORCA'
   description = 'ORCA for sonic'
   version = '1.0.0'
   base_url = 'orca'
   
config = NetBoxAccessListsConfig