import pandas

idx = pandas.Index([0,'1',3, 'fooo'])
if idx.is_mixed():
    print('mixed type')