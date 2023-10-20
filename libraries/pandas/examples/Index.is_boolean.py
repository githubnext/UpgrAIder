import pandas as pd

indx1 = pd.Index([[1, 2, 2, 3], [3, 3]])

if indx1.is_boolean():
	print("Provided index is boolean")