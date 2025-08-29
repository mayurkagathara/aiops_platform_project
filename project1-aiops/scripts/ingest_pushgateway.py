import pandas as pd
import requests, time, random, datetime

instance_name = "ac20cd"
csv_file_path = r'C:\Users\admin\Documents\VP\Week 7-8\aiops_platform_project\project1-aiops\data\nab\realAWSCloudwatch\ec2_cpu_utilization_' + instance_name + '.csv'

try:
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    # Convert timestamp column to datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'])


url = f"http://localhost:9091/metrics/job/node/instance/{instance_name}"

start = datetime.datetime.now() - datetime.timedelta(days=30)
for i, cpu_value in df.value.items():
    ts = int((start + datetime.timedelta(minutes=i)).timestamp())
    #cpu = random.uniform(10, 95)
    #mem = random.uniform(20, 90)
    requests.post(url, data=f'node_cpu_usage{{instance="{instance_name}"}} {cpu_value} {ts}\n')
    #requests.post(url, data=f'node_memory_usage{{instance="ABC"}} {mem} {ts}\n')