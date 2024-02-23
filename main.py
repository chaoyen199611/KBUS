import docplex.mp.model as cpx
import pandas as pd
from datetime import datetime,timedelta
import sys
from docplex.cp.model import *


df = pd.read_csv('route60.csv',index_col=False)
df.loc[:,'start_hour'] =df .apply(lambda x: datetime.strptime(x['去起'], '%H:%M').hour,axis=1)
df.loc[:,'去起'] = df.apply(lambda x: (datetime.strptime(x['去起'], '%H:%M')-datetime.strptime('06:00', '%H:%M')).total_seconds()/60, axis=1)
df.loc[:,'去起'] = df.apply(lambda x: (datetime.strptime(x['去迄'], '%H:%M')-datetime.strptime('06:00', '%H:%M')).total_seconds()/60, axis=1)
df.loc[:,'去起'] = df.apply(lambda x: (datetime.strptime(x['返起'], '%H:%M')-datetime.strptime('06:00', '%H:%M')).total_seconds()/60, axis=1)
df.loc[:,'去起'] = df.apply(lambda x: (datetime.strptime(x['返迄'], '%H:%M')-datetime.strptime('06:00', '%H:%M')).total_seconds()/60, axis=1)

print(df)

