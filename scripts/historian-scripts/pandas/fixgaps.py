import sys
import json
import pandas as pd
from datetime import date

# print all_files
all_files = []
all_files.append("bsf_csf/historian_anon-57322301c56e527fa7b78a1d.csv")
all_files.append("bsf_csf/historian_anon-other.csv")

#f1 = "/home/volttron/Desktop/anon/historian_anon-57322339c56e527fa7b79d93.csv"
#f2 = "/home/volttron/Desktop/prod/historian_prod-57294069c56e5232da383387.csv"
f1 = "A1.csv"
f2 = "P1.csv"
df1 = pd.read_csv(f1, index_col=None)
df2 = pd.read_csv(f2, index_col=None)
df2['ts'] = pd.to_datetime(df2['ts'])

gap = df2[(df2['ts'] > date(2016,04,05)) & (df2['ts'] <= date(2016,05,05))]
gap.to_csv('fix1.csv', index=False)
#
# cols = df.columns.tolist()                         #generate list of column names
#
# #get copies where the indeces are the columns of interest
# df2 = df.set_index(cols)
# other2 = other.set_index(cols)
# #Look for index overlap, ~
# dfx = df[~df2.index.isin(other2.index)]
#df1=df1[~df1.isin(df2)].dropna(how = 'all')
#df1.to_csv('fix.csv', index=False)