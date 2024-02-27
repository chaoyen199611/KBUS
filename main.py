import docplex.mp.model as cpx
import pandas as pd
from datetime import datetime,timedelta
import sys
from docplex.cp.model import *


df = pd.read_csv('route60.csv',index_col=False)
df.loc[:,'start_hour'] =df .apply(lambda x: datetime.strptime(x['去起'], '%H:%M').hour,axis=1)
df.loc[:,'start_0'] = df.apply(lambda x: (datetime.strptime(x['去起'], '%H:%M')-datetime.strptime('06:00', '%H:%M')).total_seconds()/60, axis=1)
df.loc[:,'end_0'] = df.apply(lambda x: (datetime.strptime(x['去迄'], '%H:%M')-datetime.strptime('06:00', '%H:%M')).total_seconds()/60, axis=1)
df.loc[:,'start_1'] = df.apply(lambda x: (datetime.strptime(x['返起'], '%H:%M')-datetime.strptime('06:00', '%H:%M')).total_seconds()/60 if pd.notnull(x['返起']) else pd.NA, axis=1)
df.loc[:,'end_1'] = df.apply(lambda x: (datetime.strptime(x['返迄'], '%H:%M')-datetime.strptime('06:00', '%H:%M')).total_seconds()/60 if pd.notnull(x['返迄']) else pd.NA, axis=1)

print(df)


from docplex.cp.model import CpoModel

tasks = [
    (5, 73),
    (75, 140)
]

# Create CPO model
model = CpoModel()

# Create interval variables for tasks with fixed start and end times
task_vars = []
for i, (start, end) in enumerate(tasks):
    task_vars.append(model.interval_var(size = end-start,start=start, end=end, name=f"task_{i}"))

# Add no-overlap constraint
for i in range(len(tasks)):
    for j in range(i + 1, len(tasks)):
        model.add(model.end_before_start(task_vars[i], task_vars[j]))

# Add objective to minimize the number of workers
workers = model.integer_var(0, len(tasks), name="workers")
for i, task in enumerate(task_vars):
    model.add(model.presence_of(task))

# Minimize the number of workers
model.add(model.minimize(workers))

# Solve the model
print("Solving model...")
msol = model.solve(TimeLimit=10)

# Print the solution
if msol:
    for i in range(1, len(tasks) + 1):
        worker_tasks = [t for t in task_vars if msol[t].get_value() == i]
        if worker_tasks:
            print(f"Worker {i}: {[msol[t].get_name() for t in worker_tasks]}")
else:
    print("No solution found within time limit.")
