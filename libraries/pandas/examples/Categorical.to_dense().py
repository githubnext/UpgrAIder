import pandas

cat = pandas.Categorical(["a", "b", "c", "a"], ordered=True)
dense_cat = cat.to_dense()
print(dense_cat)