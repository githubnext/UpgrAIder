from enum import Enum
from apiexploration.Library import Library, FunctionDiff
from dataclasses import dataclass
from dataclasses_json import dataclass_json

class DBSource(Enum):
    documentation = "doc"
    modelonly = "modelonly"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

class ProblemType(Enum):
    DEPRECATION_WARNING = "DEPRECATION_WARNING"
    ERROR = "ERROR"

@dataclass 
class RunProblem:
    type: str
    name: str
    element_name: str
    target_obj: str | None = None
 
@dataclass
class RunResult:
    problem_free: bool # true if no error or warning, false otherwise
    problem: RunProblem = None
    msg: str = None

class UpdateStatus(Enum):
    UPDATE = "UPDATE"
    NO_UPDATE = "NO_UPDATE"
    UNKNOWN = "UNKNOWN"
    NO_RESPONSE = "NO_RESPONSE"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

class FixStatus(Enum):
    FIXED = "FIXED"
    NOT_FIXED = "NOT_FIXED"
    NEW_ERROR = "NEW_ERROR"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

@dataclass_json
@dataclass
class ModelResponse:
    update_status: UpdateStatus
    references: str
    updated_code: str
    reason: str

@dataclass_json
@dataclass
class SnippetReport:
    original_file: str
    api: str
    prompt_file: str
    original_run: RunResult
    model_response: ModelResponse
    model_reponse_file: str
    num_references: int
    modified_file: str
    modified_run: RunResult
    fix_status: FixStatus
    diff: str = None

@dataclass_json
@dataclass
class Report:
    library: Library
    num_snippets: int = None
    num_apis: int = None
    db_source: str = None
    num_fixed: int = None
    num_updated: int = None
    num_updated_w_refs: int = None
    snippets: list[SnippetReport] = None
    percent_updated: float = None
    percent_updated_w_refs: float = None
    percent_fixed: float = None