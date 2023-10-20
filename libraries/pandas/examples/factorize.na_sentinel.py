import pandas as pd
import numpy as np

ar2 = np.array(['Q', 'W', 'E', np.nan, 'Q', 'Y'])
codes, uniques = pd.factorize(ar2, na_sentinel=77)
print(codes)
print(uniques)
