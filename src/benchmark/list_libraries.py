import os
import logging as log
from apiexploration.Library import Library
import json
import jsonpickle

def list_libraries():
    libraries = []
    script_dir = os.path.dirname(__file__)
    libraries_folder = os.path.join(script_dir, "../../libraries")

    for lib_dir in os.listdir(libraries_folder):
        if lib_dir.startswith('.'):
            continue
        
        lib_path = os.path.join(libraries_folder, f"{lib_dir}")
        with open(os.path.join(lib_path, "library.json"), 'r') as jsonfile:
            libinfo = json.load(jsonfile)
            library = Library(
                name=libinfo['name'], 
                ghurl=libinfo['ghurl'], 
                baseversion=libinfo['baseversion'], 
                currentversion=libinfo['currentversion'],
                path=lib_path
            )

            libraries.append(library)

    return libraries

if __name__ == "__main__":
    libraries = list_libraries()

    # the Library class is not json serializable because its reliance on OrderedDict
    # so we use jsonpickle to encode the libraries
    lib_json = jsonpickle.encode(libraries, unpicklable=False)

    print(lib_json)
    