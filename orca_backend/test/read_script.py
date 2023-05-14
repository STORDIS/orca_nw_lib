import json

with open("output.json", "r") as w:
    json_object = json.load(w)
li=[]
for obj in json_object['openconfig-interfaces:interface']:
    if "enabled" in obj["config"]:
        enabled = obj["config"]["enabled"]
    else:
        enabled = ""    
    name = obj["name"]
    state = obj["state"]["admin-status"]
    li.append({"enabled" : enabled, "name" : name, "state" : state })

print(li)    

