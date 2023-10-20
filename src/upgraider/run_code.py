import subprocess
import os
import re
import argparse
from Report import RunResult, RunProblem, ProblemType
from apiexploration.Library import Library

from dotenv import load_dotenv

load_dotenv()
script_dir = os.path.dirname(__file__)

def find_attribute_error(error_msg: str):
    attribute_err = re.search(r"AttributeError: (.*) object has no attribute (.*)\n",error_msg)
    if attribute_err is not None:
        return RunProblem(type=ProblemType.ERROR, name="AttributeError", element_name=attribute_err.group(2), target_obj=attribute_err.group(1))

    attribute_err = re.search(r"AttributeError: module (.*) has no attribute (.*)\n", error_msg)
    if attribute_err is not None:
        return RunProblem(type=ProblemType.ERROR, name="AttributeError", element_name=attribute_err.group(2), target_obj=attribute_err.group(1))

def find_type_error(error_msg: str):
    typeerror = re.search(r"TypeError: (.*) got an unexpected keyword argument (.*)\n", error_msg)
    if typeerror is not None:
        return RunProblem(type=ProblemType.ERROR, name="TypeError", element_name=typeerror.group(2), target_obj=typeerror.group(1))

def run_code(library: Library, file: str, requirements_file: str) -> RunResult:
    print(f"Running {file}...")

    problem_free = True
    run_result = RunResult(problem_free)
    
    try:
        if requirements_file is not None:
            result = subprocess.run([f"{script_dir}/run_code.sh", file, library.name, library.currentversion, requirements_file], check=True, stderr=subprocess.PIPE)
        else:
            result = subprocess.run([f"{script_dir}/run_code.sh", file, library.name, library.currentversion], check=True, stderr=subprocess.PIPE)
        
        error_msg = result.stderr.decode('utf-8')

        #usually DeprecationWarning or FutureWarning
        future_res = re.search(r"(.*\.py):(\d*): (.*)Warning: (.*) (is|has been) deprecated (.*)\n",result.stderr.decode('utf-8'))
        if future_res is not None:
            warning = RunProblem(type=ProblemType.DEPRECATION_WARNING, name=future_res.group(3), element_name=future_res.group(4))
            run_result.problem = warning
            run_result.problem_free = False
            run_result.msg = error_msg

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8')
        run_result.problem_free = False
        run_result.msg = error_msg
        
        # look for more specific errors
        if "AttributeError" in error_msg:
            run_result.problem = find_attribute_error(error_msg)
        elif "TypeError" in error_msg:
            run_result.problem = find_type_error(error_msg)

        
    return run_result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="The full path of the python file to run")

    args = parser.parse_args()

    print(run_code(f"{script_dir}/../../data/{args.file}")) 