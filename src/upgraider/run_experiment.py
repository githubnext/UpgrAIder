import os
import logging as log
from fix_lib_examples import fix_examples
from apiexploration.Library import Library
from upgraider.Report import DBSource
import json
import argparse


def main():
    threshold = 0.5
    print("Starting experiment...")
    script_dir = os.path.dirname(__file__)

    parser = argparse.ArgumentParser(description='Run upgraider on all library examples')
    parser.add_argument('--outputDir', type=str, help='directory to write output to', required=True)
    parser.add_argument("--model", type=str, help="Which model to use for fixing", default="gpt-3.5", choices=["gpt-3.5", "gpt-4"])

    args = parser.parse_args()

    libraries_folder = os.path.join(script_dir, "../../libraries")
    output_dir = args.outputDir
    model = args.model
    
    for lib_dir in os.listdir(libraries_folder):
        if lib_dir.startswith('.'):
            continue
        lib_path = os.path.join(libraries_folder, lib_dir)
        with open(os.path.join(libraries_folder, f"{lib_dir}/library.json"), 'r') as jsonfile:
            libinfo = json.loads(jsonfile.read()) 
            library = Library(
                name=libinfo['name'], 
                ghurl=libinfo['ghurl'], 
                baseversion=libinfo['baseversion'], 
                currentversion=libinfo['currentversion'],
                path=lib_path
            )

            print(f"Fixing examples for {library.name} with no references...")
            fix_examples(
                library=library,
                output_dir=os.path.join(output_dir, lib_dir, DBSource.modelonly.value),
                db_source=DBSource.modelonly.value,
                threshold=threshold,
                model = model
            )
            
            print(f"Fixing examples for {library.name} with documentation...")
            fix_examples(
                library=library,
                output_dir=os.path.join(output_dir, lib_dir, DBSource.documentation.value),
                db_source=DBSource.documentation.value,
                threshold=threshold,
                model = model
            )

if __name__ == "__main__":
    main()
