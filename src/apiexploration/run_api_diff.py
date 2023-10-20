from Library import Library, diff_api_versions
import subprocess
import jsonpickle
import os
from os import environ as env
import csv
import pandas as pd

from dotenv import load_dotenv

load_dotenv()

def main():
    script_dir = os.path.dirname(__file__)

    for lib_dir in os.listdir(os.path.join(script_dir, "../../libraries")):

        if lib_dir.startswith('.'):
            continue

        lib_path = os.path.join(script_dir, f"../../libraries/{lib_dir}")
        
        with open(os.path.join(lib_path, "library.json"), 'r') as jsonfile:
            libinfo = jsonpickle.decode(jsonfile.read()) 
            library = Library(libinfo['name'], libinfo['ghurl'], libinfo['baseversion'], libinfo['currentversion'])

            if not os.path.exists(os.path.join(script_dir, f"../../libraries/{lib_dir}/api/{library.name}_{library.baseversion}.json")):
                subprocess.run([f"{script_dir}/load_module.sh", library.name, library.baseversion], check=True)
            else:
                print(f"Skipping analyzing API of {library.name} {library.baseversion} because it already exists")
            
            if not os.path.exists(os.path.join(script_dir, f"../../libraries/{lib_dir}/api/{library.name}_{library.currentversion}.json")):
                subprocess.run([f"{script_dir}/load_module.sh", library.name, library.currentversion], check=True)
            else:
                print(f"Skipping analyzing API of {library.name} {library.currentversion} because it already exists")

            differences = diff_api_versions(library)
            library.api_diff = differences
            jsondata = jsonpickle.encode(differences,unpicklable=False, indent=3)

            # write differences to json file
            output_json_file = os.path.join(script_dir, f"../../libraries/{lib_dir}/api/", f"{library.name}_{library.baseversion}_{library.currentversion}_diff.json")
            with open(output_json_file, 'w') as jsonfile:
                jsonfile.write(jsondata)

            df = pd.read_json(jsondata)
            df.to_csv(os.path.join(script_dir, f"../../libraries/{lib_dir}/api/{library.name}_{library.baseversion}_{library.currentversion}_diff.csv"))

if __name__ == "__main__":
    main()