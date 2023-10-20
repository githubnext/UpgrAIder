#https://github.com/autogluon/autogluon/blob/3cef80b27b87987fe5ecd0be8b4b5b2ca23e7427/tabular/src/autogluon/tabular/models/tab_transformer/tab_transformer_encoder.py#L600-L600
import pandas as pd
from pandas import DataFrame
import numpy as np

def make_date(df: DataFrame, date_field: str):
    "Make sure `df[field_name]` is of the right date type."
    field_dtype = df[date_field].dtype
    if isinstance(field_dtype, pd.core.dtypes.dtypes.DatetimeTZDtype):
        field_dtype = np.datetime64
    if not np.issubdtype(field_dtype, np.datetime64):
        df[date_field] = pd.to_datetime(df[date_field], infer_datetime_format=True)

df = pd.DataFrame({
    'name': ['alice','bob','charlie'],
    'date_of_birth': ['10/25/2005','10/29/2002','01/01/2001']
})
make_date(df, 'date_of_birth')