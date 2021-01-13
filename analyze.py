import json
import io
import sys
import os

def load_masters(folder_path):
    import os
    files = [os.path.abspath(f.path) for f in os.scandir(folder_path) if f.is_file() and f.name.lower().endswith(".json")]

    master_data = {}

    for file in files:
        with io.open(file) as f:
            try:
                data = json.load(f)
                module_name = data["moduleName"]
                master_keys = set(data.keys()) - {'tenantId', 'moduleName'}
                if module_name not in master_data:
                    master_data[module_name] = data
                else:
                    for key in master_keys:
                        if type(data[key]) is list:
                            master_data[module_name][key].extend(data[key])
                        else:
                            master_data[module_name][key] = data[key]

            except Exception as ex:
                print("Failed to load file {} due to error {}\n".format(file, ex))
    
    return master_data

def main():
    if len(sys.argv) == 1:
        print ("You needs to use the analyzer as: python3 analyze.py data/<state>")
        sys.exit(1)
    # print(sys.argv)

    path = sys.argv[1]

    actions = load_masters(path + "/ACCESSCONTROL-ACTIONS-TEST/")
    roles = load_masters(path + "/ACCESSCONTROL-ROLES/")
    roles_actions = load_masters(path + "/ACCESSCONTROL-ROLEACTIONS/")

    mappings = {
        "actions": {},
        "roles": {},
        "role_actions": {}
    }
    errors = {
        "actions": [],
        "roles": [],
        "role_actions": []
    }

    actions_map = mappings["actions"]
    roles_map = mappings["roles"]
    ra_map = mappings["role_actions"]

    for act in actions["ACCESSCONTROL-ACTIONS-TEST"]["actions-test"]:
        if act["id"] in actions_map:
            errors["actions"].append("Redefined action {}:{}, {}:{}".format(act["id"], act["url"], act["id"], actions_map[act["id"]]))
        else:
            actions_map[act["id"]] = act["url"]

    
    ra_map["roles"] = {}
    ra_map["action"] = {}

    for roleaction in roles_actions["ACCESSCONTROL-ROLEACTIONS"]["roleactions"]:
        if roleaction["rolecode"] not in ra_map["roles"]:
            ra_map["roles"][roleaction["rolecode"]] = set()

        if roleaction["actionid"] not in ra_map["roles"]:
            ra_map["action"][roleaction["actionid"]] = set()

        if roleaction["actionid"] in ra_map["roles"][roleaction["rolecode"]]:
            errors["role_actions"].append("Role {} and actionid {} redefined".format(roleaction["rolecode"], roleaction["actionid"]))

        ra_map["roles"][roleaction["rolecode"]].add(roleaction["actionid"])
        ra_map["action"][roleaction["actionid"]].add(roleaction["rolecode"])

        if roleaction["actionid"] not in actions_map:
            errors["actions"].append("Role action mapping {}:{} has a action id which doesn't exists".format(roleaction["rolecode"], roleaction["actionid"]))

    for role in roles["ACCESSCONTROL-ROLES"]["roles"]:
        if role["code"] in roles_map:
            errors["roles"].append("Role {} redefined".format(role["code"]))
        
        if role["code"] not in ra_map["roles"]:
            errors["roles"].append("Role {} has no mapped actions".format(role["code"]))

    for act in actions["ACCESSCONTROL-ACTIONS-TEST"]["actions-test"]:
        if act["id"] not in ra_map["action"]:
            errors["actions"].append("Action id {} - {} has no roles mapped to it in role actions".format(act["id"], act["url"]))

    print(json.dumps(errors, indent=2))


if __name__ == "__main__":
    main()
