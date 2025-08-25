# **Project 1: AIOps Predictive Observability Platform**

## **1\. Project Overview**

This project focuses on building a self-contained AIOps pipeline for a student lab environment. The goal is to demonstrate the end-to-end process of ingesting time-series data, performing analysis for anomalies and trends, and visualizing the results. By using the Numenta Anomaly Benchmark (NAB) dataset, we can overcome the limitation of short-lived Prometheus data and provide a rich, historical dataset for analysis.

## **2\. Architectural Design**

The architecture is a simple, three-tiered setup:

1. **Data Ingestion Layer:** A Python script reads the static NAB CSV data and pushes it to Prometheus, acting as a historical data source.  
2. **Analysis Layer:** Separate Python scripts perform machine learning analysis on the data (anomaly detection, trend forecasting). The results of this analysis are pushed back to Prometheus.  
3. **Visualization Layer:** Grafana connects to Prometheus to query and visualize the original data, anomalies, and trends on a single dashboard.

## **3\. Folder and File Structure**

A clean and organized folder structure is crucial for a maintainable project.

/project1-aiops  
├── data/  
│   ├── nab/  
│   │   ├── realAWSCloudwatch/  
│   │   │   ├── ec2\_cpu\_utilization\_24ae8d.csv  
│   │   │   └── ...  
│   ├── logs/  
│   │   ├── analysis.log  
│   │   └── ingestion.log  
├── scripts/  
│   ├── ingest\_data.py  
│   ├── analyze\_anomalies.py  
│   ├── forecast\_trends.py  
├── config/  
│   ├── config.ini  
│   ├── prometheus.yml  
│   └── grafana-dashboard.json  
├── docs/  
│   ├── project\_spec.md  
│   └── architecture.png  
├── .gitignore  
├── requirements.txt  
└── README.md

## **4\. Modules and Responsibilities**

Each Python script is a modular component with a clear responsibility.

### **ingest\_data.py**

* **Responsibility:** Read data from the NAB CSV files and push it to the Prometheus Pushgateway.  
* **Key Functions:**  
  * read\_data(file\_path): Reads a CSV file and parses the timestamp and value.  
  * push\_to\_prometheus(data\_point): Uses the prometheus\_client library to create and push a gauge metric to a specified Pushgateway endpoint.  
* **Dependencies:** prometheus\_client, pandas.

### **analyze\_anomalies.py**

* **Responsibility:** Analyze the time-series data for anomalies and push the anomaly scores to Prometheus.  
* **Key Functions:**  
  * pull\_from\_prometheus(metric\_name): Fetches data from Prometheus using its API.  
  * detect\_anomalies(data): Applies a scikit-learn model like Isolation Forest to the data and returns an anomaly score for each point.  
  * push\_anomalies\_to\_prometheus(anomaly\_scores): Pushes the scores as a new metric (e.g., cpu\_anomaly\_score) to the Pushgateway.  
* **Dependencies:** prometheus\_client, requests, pandas, scikit-learn.

### **forecast\_trends.py**

* **Responsibility:** Forecast future trends based on historical data and push the forecast to Prometheus.  
* **Key Functions:**  
  * pull\_from\_prometheus(metric\_name): Fetches data from Prometheus.  
  * forecast\_trend(data): Uses the prophet library to generate a trend forecast.  
  * push\_forecast\_to\_prometheus(forecast\_data): Pushes the forecast values (e.g., cpu\_forecast\_upper, cpu\_forecast\_lower) to the Pushgateway.  
* **Dependencies:** prometheus\_client, requests, pandas, prophet.

## **5\. Execution and Workflow**

1. **Setup:**  
   * Ensure Docker is installed. Use a docker-compose.yml to set up Prometheus, Grafana, and Pushgateway.  
   * Install Python dependencies from requirements.txt.  
   * Download the NAB dataset and place it in the data/nab/ folder.  
2. **Ingestion:** Run python scripts/ingest\_data.py to populate Prometheus with the NAB data. This script can be run daily or on-demand.  
3. **Analysis:** Run python scripts/analyze\_anomalies.py and python scripts/forecast\_trends.py to perform the analysis. These scripts should be scheduled to run after data ingestion.  
4. **Visualization:** Configure Grafana to connect to the Prometheus data source. Import the grafana-dashboard.json file to automatically create the dashboard with panels for original metrics, anomaly scores, and trends.

## **6\. Logging and Exception Handling**

Robust logging and error handling are critical for a stable application.

* **Logging:** Use Python's built-in logging module. Configure a logger in each script to write to a dedicated log file in the logs/ directory. The log level should be configurable in config.ini.  
* **Example Logging:** logging.info("Starting data ingestion..."), logging.error("Failed to push data to Prometheus: %s", e).  
* **Exception Handling:**  
  * Wrap all API calls (e.g., requests.get(), push\_to\_gateway()) in try...except blocks.  
  * Catch specific exceptions (requests.exceptions.RequestException, IOError) and log detailed error messages.  
  * Include finally blocks where necessary for cleanup.

## **7\. Packaging and Dependencies**

* **Dependencies:** All dependencies will be listed in requirements.txt.  
* **Packaging:** This project will be a simple collection of scripts. For distribution, a setup.py file could be created to package the scripts, configurations, and data, making it pip-installable.
