
import importlib
import argparse
import jsonpickle
from Library import analyze_module

# This script is used to explore the API of a module and save it to a json file
# It is triggered by load_module.sh in a separate venv, so we can import the desired version of the module

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--module_name", help="The name of the module to explore")
    parser.add_argument("--module_version", help="The version of the module to explore")
    parser.add_argument("--main_venv_path", help="The path to the folder where the main venv is running from")
    args = parser.parse_args()

    module = importlib.import_module(args.module_name)
    api = analyze_module(module)

    with open(f"{args.main_venv_path}/libraries/{args.module_name}/api/{args.module_name}_{args.module_version}.json", "w") as file:
        json_obj = jsonpickle.encode(api, unpicklable=False, indent=3)
        file.write(json_obj)