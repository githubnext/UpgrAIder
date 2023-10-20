import subprocess
from dataclasses_json import dataclass_json
import jsonpickle
import enum
from collections import OrderedDict
import inspect
import os
from dataclasses import dataclass, field

@dataclass
class Parameter():
    name: str
    type: str
    default: str

@dataclass
class Function():
    name: str
    parameters: OrderedDict[Parameter]
    return_annotation: object
    
class DiffType(enum.Enum):
    '''
        Enum for the type of difference between two functions.
        Currently only supports added and removed functions and general parameter changes (Without the specific type of change)
    '''
    UNKNOWN = -1
    ADDED = 1
    REMOVED = 2
    PARAMETERS_CHANGED = 3

@dataclass
class FunctionDiff():
    old_function: Function | None
    new_function: Function | None
    diff_type: DiffType = DiffType.UNKNOWN
    
@dataclass_json
@dataclass
class Library():
    name: str
    ghurl: str
    baseversion: str
    currentversion: str
    path: str = field(default_factory=str)

@dataclass
class LibraryDiff():
    library: Library
    baseapi: list[Function] = field(default_factory=list)
    currentapi: list[Function] = field(default_factory=list)
    api_diff: list[FunctionDiff] = field(default_factory=list)

    
def load_api(library: str, filename: str):
    with open(os.path.join(os.path.dirname(__file__), f"../../libraries/{library}/api/", filename), 'r') as jsonfile:
        api = jsonpickle.decode(jsonfile.read())
    return api

def diff_api_versions(library: Library):
    '''
        Finds differences betweeen a library's base and current api
        @param library: the library to analyze
        @return: a list of FunctionDiff objects. 
    '''
    base_api = load_api(library.name, f"{library.name}_{library.baseversion}.json")
    current_api = load_api(library.name, f"{library.name}_{library.currentversion}.json")
    differences = []

    #compare functions in baseapi and currentapi
    for old_fn_name in base_api.keys():
        if old_fn_name not in current_api.keys():
            print(f"Function {old_fn_name} has been removed")
            diff = FunctionDiff(base_api[old_fn_name], None, DiffType.REMOVED)
            differences.append(diff)
        else:
            old_function = base_api[old_fn_name]
            new_function = current_api[old_fn_name]

            if old_function['parameters'].keys() != new_function['parameters'].keys():
                print(f"Function {old_fn_name} has changed parameters")
                diff = FunctionDiff(old_function, new_function, DiffType.PARAMETERS_CHANGED)
                differences.append(diff)
            

    #find new added functions in currentapi
    new_functions = set(current_api.keys()).difference(set(base_api.keys()))
    for new_fn_name in new_functions:
        print(f"Function {new_fn_name} has been added")
        diff = FunctionDiff(None, current_api[new_fn_name], DiffType.ADDED)
        differences.append(diff)

    return differences

def analyze_signature(callable, fqn: str) -> dict:
    '''
        Analyze the signature of a function or class constructor (must be a callable object)
        @param callable: the callable object
        @param fqn: the fully qualified name of the callable object
        @return: a dictionary with a single function; the key is the fqn and the value is the Function object
    '''

    try:
        signature = inspect.signature(callable)
    except ValueError:
        print("WARN: Could not get signature for function: ", fqn)
        return {}

    parameters = OrderedDict()
    for param_name, param in signature.parameters.items():
        parameter = Parameter(param_name, param.annotation, param.default)
        parameters.update({param_name: parameter})

    function = Function(fqn, parameters, signature.return_annotation)
    return {fqn: function}

def get_functions(python_class) -> dict:
    '''
        Get all member functions of a class
        @param python_class: the class to analyze
        @return: a dictionary of all functions in the class; key is the fqn and the value is the Function object
    '''
    api = {}
    for name, data in inspect.getmembers(python_class, inspect.isfunction):
        if name.startswith("_"):
            continue
        fqn = ".".join([python_class.__module__, python_class.__name__, name])
        api.update(analyze_signature(data, fqn))
    return api

def analyze_class(python_class, fqn):
    '''
        Analyze a class and return a dictionary of all functions in the class, including the constructor
        @param python_class: the class to analyze
        @param fqn: the fully qualified name of the class
        @return: a dictionary of all functions in the class, including constructors; key is the fqn and the value is the Function object
    '''
    api = {}
    api.update(analyze_signature(python_class, fqn))
    api.update(get_functions(python_class))
    return api

def analyze_module(module):
    '''
        Analyze a module and return a dictionary of all functions in the module and its classes
        @param module: the module to analyze
        @return: a dictionary of all functions in the module and its classes; key is the fqn and the value is the Function object
    '''
    api = {}
    
    for name, data in inspect.getmembers(module):
        if inspect.isclass(data):
            fqn = ".".join([module.__name__, name])
            api.update(analyze_class(data,fqn) )

        elif inspect.isfunction(data):
            fqn = ".".join([module.__name__, name])
            api.update(analyze_signature(data, fqn))


    return api


   
    

