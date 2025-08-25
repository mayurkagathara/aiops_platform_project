import logging
import pandas as pd
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prophet import Prophet
import requests
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('../config/config.ini')

PROMETHEUS_GATEWAY = config['Prometheus']['PushGateway']
PROMETHEUS_API = config['Prometheus']['API']
LOG_FILE = '../data/logs/forecast.log'

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def pull_from_prometheus(metric_name):
    """Fetches data from Prometheus."""
    try:
        response = requests.get(f"{PROMETHEUS_API}/api/v1/query", params={"query": metric_name})
        response.raise_for_status()
        data = response.json()['data']['result']
        logging.info("Data pulled from Prometheus for metric: %s", metric_name)
        return pd.DataFrame(data)
    except Exception as e:
        logging.error("Error pulling data from Prometheus: %s", e)
        raise

def forecast_trend(data):
    """Forecasts trends using Prophet."""
    try:
        model = Prophet()
        data = data.rename(columns={"timestamp": "ds", "value": "y"})
        model.fit(data)
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)
        logging.info("Trend forecasting completed.")
        return forecast
    except Exception as e:
        logging.error("Error during trend forecasting: %s", e)
        raise

def push_forecast_to_prometheus(forecast_data):
    """Pushes forecast data to Prometheus."""
    try:
        registry = CollectorRegistry()
        gauge = Gauge('forecast', 'Forecast Data', registry=registry)
        for _, row in forecast_data.iterrows():
            gauge.set(row['yhat'])
            push_to_gateway(PROMETHEUS_GATEWAY, job='trend_forecast', registry=registry)
        logging.info("Forecast data pushed to Prometheus.")
    except Exception as e:
        logging.error("Failed to push forecast data to Prometheus: %s", e)
        raise

if __name__ == "__main__":
    metric_name = 'nab_metric'
    data = pull_from_prometheus(metric_name)
    forecast = forecast_trend(data)
    push_forecast_to_prometheus(forecast)
