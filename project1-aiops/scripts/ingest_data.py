# import logging
# import pandas as pd
# from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
# import configparser
# from datetime import datetime
# import time
# import json
# import requests
# import snappy
# from prometheus_remote_writer import RemoteWriter

# # Load configuration
# config = configparser.ConfigParser()
# config.read('../config/config.ini')

# PROMETHEUS_GATEWAY = config['Prometheus']['PushGateway']
# PROMETHEUS_API = config['Prometheus']['API']
# LOG_FILE = '../data/logs/ingestion.log'
# METRIC_NAME = 'nab_aws_cpu'

# # Configure logging
# logging.basicConfig(
#     filename=LOG_FILE,
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )

# def read_data(file_path):
#     """Reads a CSV file, updates the timestamp to the current year, and parses the value."""
#     try:
#         data = pd.read_csv(file_path)
#         logging.info("Data read successfully from %s", file_path)

#         # Ensure the timestamp column is in datetime format
#         data['timestamp'] = pd.to_datetime(data['timestamp'])

#         # Update the year to the current year (2025)
#         current_year = datetime.now().year
#         data['timestamp'] = data['timestamp'].apply(lambda x: x.replace(year=current_year))

#         logging.info("Timestamps updated to the current year: %d", current_year)
#         return data
#     except Exception as e:
#         logging.error("Error reading or processing data from %s: %s", file_path, e)
#         raise

# def push_to_prometheus(value):
#     """Pushes a data point to Prometheus Pushgateway."""
#     try:
#         registry = CollectorRegistry()
#         gauge = Gauge(METRIC_NAME, 'NAB Metric', registry=registry)
#         gauge.set(value)
#         push_to_gateway(PROMETHEUS_GATEWAY, job='ingestion', registry=registry)
#         logging.info("Data pushed to Prometheus: value=%s", value)
#     except Exception as e:
#         logging.error("Failed to push data to Prometheus: %s", e)
#         raise

# def push_to_prometheus_remote_writer(data):
#     """Pushes historical data to Prometheus using prometheus-remote-writer and snappy."""
#     try:
#         writer = RemoteWriter(
#             url=f"{PROMETHEUS_API}/api/v1/write",
#             # headers={"Content-Encoding": "snappy"}
#         )

#         # Prepare the payload
#         metrics = [
#             {
#                 'metric': {'__name__': METRIC_NAME, 'instance': 'ec2_cpu_utilization_ac20cd'},
#                 'values': data['value'].tolist(),
#                 'timestamps': data['timestamp'].apply(lambda x: int(x.timestamp() * 1000)).tolist()
#             }
#         ]
#         print(metrics[:5])

#         # Send the data
#         writer.send(metrics)

#         logging.info("Historical data pushed to Prometheus successfully using prometheus-remote-writer.")
#     except Exception as e:
#         logging.error("Failed to push historical data to Prometheus: %s", e)
#         raise

# if __name__ == "__main__":
#     file_path = r'C:\Users\admin\Documents\VP\Week 7-8\aiops_platform_project\project1-aiops\data\nab\realAWSCloudwatch\ec2_cpu_utilization_ac20cd.csv'  # Example file path
#     data = read_data(file_path)

#     # Sort data by timestamp to ensure correct order
#     data = data.sort_values(by='timestamp')

#     # Push historical data
#     push_to_prometheus_remote_writer(data)

##########ONLY backfill worked ##########

import pandas as pd
from datetime import datetime
# --- Configuration ---
csv_file_path = r'C:\Users\admin\Documents\VP\Week 7-8\aiops_platform_project\project1-aiops\data\nab\realAWSCloudwatch\ec2_cpu_utilization_ac20cd.csv'
output_file_path = 'metrics.om'
metric_name = 'numenta_cpu_aws'
# Add any labels you want to associate with the metric
labels = {'job': 'numenta_import', 'instance': 'cloudwatch_benchmark'}

# --- Script Logic ---
print(f"Reading data from '{csv_file_path}'...")
try:
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    # Convert timestamp column to datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    current_year = datetime.now().year
    df['timestamp'] = df['timestamp'].apply(lambda x: x.replace(year=current_year))

except FileNotFoundError:
    print(f"Error: The file '{csv_file_path}' was not found.")
    exit()

# Create the label string for OpenMetrics format
label_str = "{" + ",".join([f'{k}="{v}"' for k, v in labels.items()]) + "}"

print(f"Converting data to OpenMetrics format...")
with open(output_file_path, 'w') as f:
    for index, row in df.iterrows():
        # Convert timestamp to Unix timestamp in milliseconds
        timestamp_ms = int(row['timestamp'].timestamp())
        value = row['value']

        # Write the formatted line to the output file
        f.write(f"{metric_name}{label_str} {value} {timestamp_ms}\n")

    # Add the # EOF to signify the end of the file
    f.write("# EOF\n")

print(f"✅ Successfully created OpenMetrics file at '{output_file_path}'")  # Example file path