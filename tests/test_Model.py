from upgraider.Model import UpdateStatus, parse_model_response


def test_correctly_formatted_response():
    reference = "32639"
    updated_code = """
import numpy as np

import pandas as pd

cat = pd.Categorical(["a", "b", "c", "a"], ordered=True)
dense_cat = np.asarray(cat)
print(dense_cat)
"""
    reason = "The method Categorical.to_dense() has been deprecated and replaced with np.asarray(cat)."

    response = f"""
1. ```{updated_code}```
2. {reason}
3. {reference}
    """

    result = parse_model_response(response)
    assert result.update_status == UpdateStatus.UPDATE
    assert result.references == reference
    assert result.updated_code == updated_code.strip()
    assert result.reason == reason

def test_incorrect_short_repsonse():
    reference = "No references used"

    response = f"""
{reference}
    """

    result = parse_model_response(response)
    assert result.update_status == UpdateStatus.NO_RESPONSE

def test_incorrect_long_repsonse():
    response = """
    No updates needed.
Reason: The code is using valid and up-to-date numpy APIs to create an array and sort it. No deprecated or non-existent APIs are being used.
References used: No references used.
"""
    result = parse_model_response(response)

    assert result.update_status == UpdateStatus.NO_UPDATE
    assert result.references is None

def test_reason_not_enumerated():
    reason = "Here is the model's reason."
    references = "3"
    response= f"""
Possible response:

```
some code
```

Reason for update: {reason}

List of reference numbers used: {references}
"""

    result = parse_model_response(response)
    assert result.update_status == UpdateStatus.UPDATE
    assert result.reason == reason
    assert result.references == references

def test_reason_enumerated():
    reason = "Here is the model's reason."
    reference = "3"
    response= f"""
Possible response:

```
some code
```

2. {reason}
3. {reference}
"""
    result = parse_model_response(response)
    assert result.update_status == UpdateStatus.UPDATE
    assert result.reason == reason
    assert result.references == reference

def test_no_reason():
    response= f"""
```
some code
```

- Reason for update: None
- List of reference numbers used: No references used
"""
    result = parse_model_response(response)
    assert result.update_status == UpdateStatus.UPDATE
    assert result.reason is None
    assert result.references is None

def test_codeexists_but_not_updated():
    response = f"""
Possible response:

```
# No changes needed
import pandas as pd
some code
```

- Reason for update: None
- List of reference numbers used: No references used
"""
    result = parse_model_response(response)
    assert result.update_status == UpdateStatus.NO_UPDATE
    assert result.reason is None
    assert result.references is None

def test_enumerated_reason():
    reason1 = "reason 1"
    reason2 = "reason 2"
    response= f"""
```
some code
```

Reason for update:

- {reason1}
- {reason2}

List of reference numbers used:

- 6
"""
    result = parse_model_response(response)
    assert result.update_status == UpdateStatus.UPDATE
    assert result.reason == f"- {reason1}\n- {reason2}"
