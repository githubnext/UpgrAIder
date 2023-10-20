import pandas as pd

# Create multiple lists
technologies =  ['Spark','Pandas','Java','Python', 'PHP']
fee = [25000,20000,15000,15000,18000]
duration = ['5o Days','35 Days','40 days','30 Days', '30 Days']
discount = [2000,1000,800,500,800]
columns=['Courses','Fee','Duration','Discount']

# Create DataFrame from multiple lists
df = pd.DataFrame(list(zip(technologies,fee,duration,discount)), columns=columns)

writer = pd.ExcelWriter('output.xlsx')
df.to_excel(writer, sheet_name='Sheet1')
writer.save()

