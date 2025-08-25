import logging
from urllib import response
import pandas as pd
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from sklearn.ensemble import IsolationForest
import requests
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('../config/config.ini')

PROMETHEUS_GATEWAY = config['Prometheus']['PushGateway']
PROMETHEUS_API = config['Prometheus']['API']
LOG_FILE = '../data/logs/analysis.log'

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def pull_from_prometheus(metric_name):
    """Fetches data from Prometheus and preprocesses it."""
    try:
        response = requests.get(f"{PROMETHEUS_API}/api/v1/query_range", params={"query": 'numenta_cpu_aws{instance="cloudwatch_benchmark"}', "start":"1754604140", "end":"1755814940", "step":"300.0"})
        response.raise_for_status()
        results = response.json()['data']['result']

        # Log the raw data structure for debugging
        logging.debug("Raw data from Prometheus: %s", results[:5])

        # Preprocess the data to extract 'timestamp' and 'value'
        data = []
        for result in results:
            if 'values' in result:
                for value in result['values']:
                    data.append({"timestamp": value[0], "value": float(value[1])})

        if not data:
            logging.error("No valid data found for metric: %s", metric_name)
            raise ValueError("No data available for the specified metric.")

        df = pd.DataFrame(data)
        logging.info("Data pulled and preprocessed from Prometheus for metric: %s", metric_name)
        return df
    except Exception as e:
        logging.error("Error pulling data from Prometheus: %s", e)
        raise

def detect_anomalies(data):
    """Detects anomalies using Isolation Forest."""
    try:
        print(data)
        model = IsolationForest()
        data['anomaly_score'] = model.fit_predict(data[['value']])
        logging.info("Anomaly detection completed.")
        return data
    except Exception as e:
        logging.error("Error during anomaly detection: %s", e)
        raise

def push_anomalies_to_prometheus(anomaly_scores):
    """Pushes anomaly scores to Prometheus."""
    try:
        registry = CollectorRegistry()
        gauge = Gauge('aws_cpu_anomaly_score', 'Anomaly Score', registry=registry)
        for score in anomaly_scores:
            gauge.set(score)
            push_to_gateway(PROMETHEUS_GATEWAY, job='anomaly_analysis', registry=registry)
        logging.info("Anomaly scores pushed to Prometheus.")
    except Exception as e:
        logging.error("Failed to push anomaly scores to Prometheus: %s", e)
        raise

if __name__ == "__main__":
    metric_name = 'aws_cpu'
    data = pull_from_prometheus(metric_name)
    anomalies = detect_anomalies(data)
    push_anomalies_to_prometheus(anomalies['anomaly_score'])
