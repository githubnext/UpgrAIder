import os
import sys


# Insert the root of the project into the path so we can import from
# the `tests` package.
root_path = os.path.abspath(os.path.join(__file__, "..", ".."))
sys.path.insert(0, root_path)
