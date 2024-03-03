import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from docplex.cp.model import CpoModel
from datetime import datetime,timedelta
from itertools import combinations


tasks = pd.read_csv('route_test.csv',index_col=False)
tasks.loc[:,"name"] = tasks['start']+'_'+tasks['direction'].astype(str)
tasks.loc[:,'start'] = tasks.apply(lambda x: (datetime.strptime(x['start'], '%H:%M')-datetime.strptime('06:00', '%H:%M')).total_seconds()/60 if pd.notnull(x['start']) else pd.NA, axis=1)
tasks.loc[:,'end'] = tasks.apply(lambda x: (datetime.strptime(x['end'], '%H:%M')-datetime.strptime('06:00', '%H:%M')).total_seconds()/60 if pd.notnull(x['end']) else pd.NA, axis=1)

print(tasks)


# tasks = {
#     "start": [20.0, 5.0,
#             45.0, 20.0,
#             60,35,
#             75,50,
#             90,65,
#             105,95,
#             135,120,
#             150,145],
#     "end": [85.0, 73.0,
#             110.0, 88.0,
#             125,103,
#             140,118,
#             155,133,
#             170,163,
#             200,188,
#             215,213],
#     "direction": [0, 1, 0, 1, 0,1,0,1,0,1,0,1,0,1,0,1],
#     "name": ["06:20_0", "06:05_1", "06:45_0", "06:20_1","07:00_0",
#             "06:35_1","07:15_0","06:50_1","07:30_0","07:05_1",
#             "07:45_0","07:35_1","08:15_0","08:00_1","08:30_0","08:25_1"]
# }

# tasks = pd.DataFrame(tasks)

# Sample buses
buses = ["bus1", "bus2", "bus3","bus4","bus5","bus6","bus7","bus8","bus9","bus10",
         "bus11", "bus12", "bus13","bus14","bus15","bus16","bus17","bus18","bus19","bus20"]

# Create a model
model = CpoModel()

# Decision variables: task assignment to buses
assign = {}
for index, task in tasks.iterrows():
    for worker_name in buses:
        assign[(index, worker_name)] = model.binary_var(name=f"assign_{index}_{worker_name}")

# Constraints: each task is assigned to exactly one worker
for index, task in tasks.iterrows():
    model.add(sum(assign[(index, worker_name)] for worker_name in buses) == 1)

# Constraints: tasks assigned to a worker do not overlap
for worker_name in buses:
    for i, j in combinations(range(len(tasks)), 2):
        if i < j:
            if (tasks.iloc[i]["end"] > tasks.iloc[j]["start"]) or (tasks.iloc[i]["start"] < tasks.iloc[j]["end"]):
                model.add(((assign[(i, worker_name)] + assign[(j, worker_name)] <= 1)))
            model.add(((assign[(i, worker_name)] + assign[(j, worker_name)] <= 1))|
                        (assign[(i, worker_name)] + assign[(j, worker_name)] == 2) & 
                      ((assign[(i, worker_name)] * tasks.iloc[i]["direction"] +
                        assign[(j, worker_name)] * tasks.iloc[j]["direction"]) == 1))
                


# # Constraints: consecutive tasks assigned to a worker have alternating directions
# for worker_name in buses:
#     for i in range(len(tasks)-1):
#         for j in range(i+1,len(tasks)):
            

# Define a set of buses who have been assigned tasks
assigned_workers = [model.sum(assign[(index, worker_name)] for index, _ in tasks.iterrows()) >= 1 for worker_name in buses]

# Objective: minimize the number of buses who have been assigned tasks
model.minimize(model.sum(assigned_workers))

# Solve the model
print("Solving model...")
msol = model.solve()

# Print solution
if msol:
    print("Minimum buses needed:", msol.get_objective_values()[0])
    for worker_name in buses:
        for index, task in tasks.iterrows():
            if msol.get_value(assign[(index, worker_name)]) == 1:
                print(f"Task {task['name']} assigned to {worker_name}")
else:
    print("No solution found.")
    



# Extract task assignments from the solution
assigned_tasks = {worker_name: [] for worker_name in buses}
for worker_name in buses:
    for index, task in tasks.iterrows():
        if msol.get_value(assign[(index, worker_name)]) == 1:
            assigned_tasks[worker_name].append((task["start"], task["end"], task["name"]))

    
    
fig, ax = plt.subplots()
for i, (worker_name, tasks_assigned) in enumerate(assigned_tasks.items()):
    for j, task in enumerate(tasks_assigned):
        start, end, name = task
        ax.barh(y=i, left=start, width=end-start, height=0.3, align='center', color='blue', alpha=0.6)
        ax.text(start + (end - start) / 2, i + 0.15, name, ha='center', va='center', color='black')
ax.set_yticks(np.arange(len(buses)))
ax.set_yticklabels(buses)
ax.set_xlim(0, max(tasks["end"]))
ax.set_xlabel("Time")
ax.set_ylabel("Worker")
ax.set_title("Task Assignment for buses")
ax.invert_yaxis()  # Invert y-axis to show buses at the top
plt.show()


