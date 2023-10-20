
import argparse
from upgraider.Report import Report, SnippetReport, UpdateStatus, RunResult, FixStatus
from upgraider.run_code import run_code
from upgraider.Model import fix_suggested_code 
import os
import json
import difflib
from apiexploration.Library import Library
from enum import Enum
import ast
from collections import namedtuple, defaultdict
import time

class ResultType(Enum):
    PROMPT = 1
    RESPONSE = 2

Import = namedtuple("Import", ["module", "name", "alias"])

def _write_result(result: str, result_type:ResultType, output_dir: str, example_file: str):
    result_file_root = os.path.splitext(example_file)[0]

    if result_type == ResultType.RESPONSE:
        result_file = os.path.join(output_dir, f"responses/{result_file_root}_response.txt")
    elif result_type == ResultType.PROMPT:
        result_file = os.path.join(output_dir, f"prompts/{result_file_root}_prompt.txt")
    else:
        print(f"Invalid result type: {result_type}")
        return 
    
    os.makedirs(os.path.dirname(result_file), exist_ok=True)
    with open(result_file, 'w') as f:
        f.write(result)
    return result_file

def _determine_fix_status(original_code_result: RunResult, final_code_result: RunResult) -> FixStatus:
    # original status is always an error or warning
    if final_code_result.problem_free == True:
        return FixStatus.FIXED
    else:
        if original_code_result.problem != final_code_result.problem:
            return FixStatus.NEW_ERROR
        else:
            return FixStatus.NOT_FIXED

#https://stackoverflow.com/questions/845276/how-to-print-the-comparison-of-two-multiline-strings-in-unified-diff-format
#https://stackoverflow.com/posts/845432/, Andrea Francia
def _unidiff(expected, actual):
    """
    Helper function. Returns a string containing the unified diff of two multiline strings.
    """
    expected=expected.splitlines(1)
    actual=actual.splitlines(1)

    diff=difflib.unified_diff(expected, actual)

    return ''.join(diff)

def _format_import(import_stmt: Import) -> str:
    if import_stmt.module:
        if import_stmt.alias is not None:
            return f"from {'.'.join(import_stmt.module)} import {'.'.join(import_stmt.name)} as {import_stmt.alias}"
        else:
            return f"from {'.'.join(import_stmt.module)} import {'.'.join(import_stmt.name)}"
    else:
        if import_stmt.alias is not None:
            return f"import {'.'.join(import_stmt.name)} as {import_stmt.alias}"
        else:
            return f"import {'.'.join(import_stmt.name)}"

# GaretJax, https://stackoverflow.com/questions/9008451/python-easy-way-to-read-all-import-statements-from-py-module  
def _get_imports(code: str) -> list[Import]:
    try:
        ast_root = ast.parse(code)

        for node in ast.iter_child_nodes(ast_root):
            if isinstance(node, ast.Import):
                module = []
            elif isinstance(node, ast.ImportFrom):  
                module = node.module.split('.')
            else:
                continue

            for n in node.names:
                yield Import(module, n.name.split('.'), n.asname)
    except:
        return None

def _fix_imports(old_code: str, updated_code: str) -> str:
    old_imports = _get_imports(old_code)
    updated_imports = _get_imports(updated_code)

    if old_imports is None or updated_imports is None:
        print("WARNING: could not parse imports for either old or updated code")
        return updated_code

    # if there is an old import that is not in the updated code, add it
    for old_import in old_imports:
        if old_import not in updated_imports:
            updated_code = f"{_format_import(old_import)}\n{updated_code}"

    return updated_code


def fix_example(library: Library, 
        example_file: str, 
        examples_path: str, 
        requirements_file: str, 
        output_dir: str, 
        db_source: str, 
        model: str = 'gpt3-5',
        threshold:float = None):

    example_file_path = os.path.join(examples_path, example_file)

    print(f"Fixing {example_file_path}...")
    with open(example_file_path, 'r') as f:
        original_code = f.read()

    original_code_result = run_code(library, example_file_path, requirements_file)

    prompt_text, model_response, parsed_response, ref_count = fix_suggested_code(original_code, show_prompt=False, db_source=db_source, model=model, threshold=threshold)

    print("Writing prompt to file...")
    prompt_file = _write_result(prompt_text, ResultType.PROMPT, output_dir, example_file)

    print("Writing model response to file...")
    model_response_file = _write_result(model_response, ResultType.RESPONSE, output_dir, example_file)

    final_code_result = None # will stay as None if no update occurs
    updated_code_file = None
    diff = None
    updated_code = None
    example_file_root = os.path.splitext(example_file)[0]

    if parsed_response.update_status == UpdateStatus.UPDATE:
        updated_code = parsed_response.updated_code
        if updated_code is None:
            print(f"WARNING: update occurred for {example_file} but could not retrieve updated code")
        else:
            updated_code = _fix_imports(old_code=original_code, updated_code=updated_code)
            updated_code_file = os.path.join(output_dir, f"updated/{example_file_root}_updated.py")
            os.makedirs(os.path.dirname(updated_code_file), exist_ok=True)
            with open(updated_code_file, 'w') as f:
                f.write(updated_code)

            final_code_result = run_code(library, updated_code_file, requirements_file)
            diff = _unidiff(original_code, updated_code)

    snippet_results = SnippetReport(
        original_file=example_file,
        api=example_file_root, # for now, file name is in format <api>.py
        prompt_file=prompt_file,
        num_references=ref_count,
        modified_file=updated_code_file,
        original_run=original_code_result,
        model_response=parsed_response,
        model_reponse_file=model_response_file,
        modified_run=final_code_result,
        fix_status=_determine_fix_status(original_code_result, final_code_result) if final_code_result is not None else FixStatus.NOT_FIXED,
        diff=diff
    )

    return snippet_results


def fix_examples(library: Library, output_dir: str, db_source: str, model:str, threshold: float = None):
    print(f"=== Fixing examples for {library.name} with model {model}")

    report = Report(library)
    snippets = {}
    examples_path = os.path.join(library.path, "examples")

    if os.path.exists(examples_path):
        requirements_file = os.path.join(library.path, "requirements.txt")

        if not os.path.exists(requirements_file):
            requirements_file = None

        for example_file in os.listdir(examples_path):
            if example_file.startswith('.'):
                continue

            snippet_results = fix_example(library=library, example_file=example_file, examples_path=examples_path, requirements_file=requirements_file, output_dir=output_dir, db_source=db_source, model=model, threshold=threshold)

            print(f"Finished fixing {example_file}...")
            snippets[example_file] = snippet_results

            # wait 30 seconds between each example
            time.sleep(30)

    report.snippets = snippets
    report.num_snippets = len(snippets)
    report.db_source = db_source
    report.num_fixed = len([s for s in snippets.values() if s.fix_status == FixStatus.FIXED])
    report.num_updated = len([s for s in snippets.values() if s.model_response.update_status == UpdateStatus.UPDATE])
    report.num_updated_w_refs = len([s for s in snippets.values() if s.model_response.update_status == UpdateStatus.UPDATE and s.model_response.references is not None and 'No references used' not in s.model_response.references])
    report.num_apis = len(set([s.api for s in snippets.values()]))

    output_json_file = os.path.join(output_dir, "report.json")
    jsondata =  report.to_json(indent=4)
    os.makedirs(os.path.dirname(output_json_file), exist_ok=True)
    with open(output_json_file, 'w') as jsonfile:
        jsonfile.write(jsondata)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fix example(s) for a given library')
    parser.add_argument('--libpath', type=str, help='absolute path of target library folder', required=True)
    parser.add_argument('--outputDir', type=str, help='absolute path of directory to write output to', required=True)
    parser.add_argument('--dbsource', type=str, help='Which database to use for retrieval, doc (documentation) or modelonly to not augment with retrieval', required=True)
    parser.add_argument('--threshold', type=float, help='Similarity Threshold for retrieval')
    parser.add_argument('--examplefile', type=str, help='Specific example file to run on (optional). Only name of example file needed.', required=False)
    parser.add_argument("--model", type=str, help="Which model to use for fixing", default="gpt-3.5", choices=["gpt-3.5", "gpt-4"])

    args = parser.parse_args()
    script_dir = os.path.dirname(__file__)

    with open(os.path.join(args.libpath, "library.json"), 'r') as jsonfile:
        libinfo = json.loads(jsonfile.read()) 
        library = Library(
            name=libinfo['name'], 
            ghurl=libinfo['ghurl'], 
            baseversion=libinfo['baseversion'], 
            currentversion=libinfo['currentversion'],
            path=args.libpath
        )
        output_dir = os.path.join(script_dir, args.outputDir)

        if args.examplefile is not None:
            # fix a specific example
            fix_example(library=library, example_file=args.examplefile, examples_path=os.path.join(library.path, "examples"), requirements_file=os.path.join(library.path, "requirements.txt"), output_dir=output_dir, db_source=args.dbsource, model=args.model, threshold=args.threshold)
        else:
            # fix all examples for this library
            fix_examples(library=library, output_dir=output_dir, model=args.model, db_source=args.dbsource, threshold=args.threshold)
