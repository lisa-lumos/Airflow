from airflow import DAG
from datetime import datetime, timedelta

# see a list of providers here:
# https://airflow.apache.org/docs/apache-airflow-providers/packages-ref.html
from airflow.sensors.http_sensor import HttpSensor
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator

import csv
import requests
import json

# create a default args dict
default_args = {
  "owner": "airflow", # the owner of all the tasks in the dag
  "email_on_failure": False, 
  "email_on_retry": False,
  "email": "admin@email.com", # if emails enabled, the target email address
  "retries": 1, # if task fails, will be retried once, before being announced as failure
  "retry_delay": timedelta(minutes=5) # wait 5min before retrying
}

# Download forex rates according to the currencies we want to watch
# -------- described in the file forex_currencies.csv:
# base;with_pairs
# EUR;USD NZD JPY GBP CAD
# USD;EUR NZD JPY GBP CAD
# -------- An api response example:
# {
#   "rates":{"CAD":1.21,"GBP":0.36,"JPY":101.89,"USD":1.13,"NZD":1.41,"EUR":1.0},
#   "base":"EUR",
#   "date":"2021-01-01"
# }
# -------- The output file looks like this:
# {"base": "EUR", "rates": {"USD": 1.13, "NZD": 1.41, "JPY": 101.89, "GBP": 0.36, "CAD": 1.21}, "last_update": "2021-01-01"}
# {"base": "USD", "rates": {"EUR": 0.9, "NZD": 1.52, "JPY": 108.56, "GBP": 0.76, "CAD": 1.31}, "last_update": "2021-01-01"}
def download_rates():
    BASE_URL = "https://gist.githubusercontent.com/marclamberti/f45f872dea4dfd3eaa015a4a1af4b39b/raw/"
    ENDPOINTS = {
        'USD': 'api_forex_exchange_usd.json',
        'EUR': 'api_forex_exchange_eur.json'
    }
    with open('/opt/airflow/dags/files/forex_currencies.csv') as forex_currencies:
        reader = csv.DictReader(forex_currencies, delimiter=';')
        for idx, row in enumerate(reader):
            base = row['base']
            with_pairs = row['with_pairs'].split(' ')
            indata = requests.get(f"{BASE_URL}{ENDPOINTS[base]}").json()
            outdata = {'base': base, 'rates': {}, 'last_update': indata['date']}
            for pair in with_pairs:
                outdata['rates'][pair] = indata['rates'][pair]
            with open('/opt/airflow/dags/files/forex_rates.json', 'a') as outfile:
                json.dump(outdata, outfile)
                outfile.write('\n')


# this dag will be triggered daily at midnight
with DAG(
  "forex_data_pipeline",            # the dag id, need to be unique across all dags
  start_date=datetime(2024, 3, 25), # when the dag will be scheduled
  schedule_interval="@daily",       # how often the dag will be triggered, takes CRON
  default_args=default_args,        # args for the tasks in the dag
  catchup=False                     # cannot run all the non triggered dag runs,
                                    # between start date and today
) as dag: 
  
  # Check if the API is available - HttpSensor
  # the url to check is:
  # https://gist.github.com/marclamberti/f45f872dea4dfd3eaa015a4a1af4b39b
  is_forex_rates_available = HttpSensor(
    task_id='is_forex_rates_available', # must be unique in this dag
    http_conn_id='forex_api',
    endpoint="marclamberti/f45f872dea4dfd3eaa015a4a1af4b39b", # after host name
    response_check=lambda response: "rates" in response.text, # if rates in response
    poke_interval=5, # check every 5 secs
    timeout=20 # if 20 secs later, still not available, then task ends in failure, should always specify it, as a best practice
  )

  # Check if the currency file is available - FileSensor
  # checks every 1 min to see if a file/folder exist 
  # in a specific location, in the file system
  # Apache Airflow documentation -> References -> Python API -> 
  # Operators packages -> airflow.sensors -> airflow.sensors.filesystem
  # It checks this file: /opt/airflow/dags/files/forex_currencies.csv
  # and maps to this in the local machine: mnt/airflow/dags/files/forex_currencies.csv
  is_forex_currencies_file_available = FileSensor(
    task_id="is_forex_currencies_file_available",
    fs_conn_id="forex_path",
    filepath="forex_currencies.csv",
    poke_interval=5,
    timeout=20
  )

  # Apache Airflow documentation -> References -> Python API -> 
  # Operators packages -> airflow.operators -> airflow.operators.python
  downloading_rates = PythonOperator(
    task_id="downloading_rates",
    python_callable=download_rates
  )

  # Assume the output file is huge, 
  # so you need to put this file in a distributed file system, 
  # such as a HDFS
  # In the browser, go to http://localhost:32762
  # This takes you to HUE, to access the HDFS
  # use "root" for both username and pwd
  # Click on Files icon in the left bar
  # go to root, and see the files/folders in the HDFS
  # test this task, then refresh this browser page,
  # should see /forex/forex_rates.json
  saving_rates = BashOperator(
    task_id="saving_rates",
    bash_command="""
      hdfs dfs -mkdir -p /forex && \
      hdfs dfs -put -f $AIRFLOW_HOME/dags/files/forex_rates.json /forex
    """
  )