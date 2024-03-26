from airflow import DAG
from datetime import datetime, timedelta

# see a list of providers here:
# https://airflow.apache.org/docs/apache-airflow-providers/packages-ref.html
from airflow.providers.http.sensors.http import HttpSensor

# create a default args dict
default_args = {
  "owner": "airflow", # the owner of all the tasks in the dag
  "email_on_failure": False, 
  "email_on_retry": False,
  "email": "admin@email.com", # if emails enabled, the target email address
  "retries": 1, # if task fails, will be retried once, before being announced as failure
  "retry_delay": timedelta(minutes=5) # wait 5min before retrying
}

# this dag will be triggered daily at midnight
with DAG(
  "forex_data_pipeline",            # the dag id, need to be unique across all dags
  start_date=datetime(2024, 3, 25), # when the dag will be scheduled
  schedule_interval="@daily",       # how often the dag will be triggered, takes CRON
  default_args=default_args,        # args for the tasks in the dag
  catchup=False                     # cannot run all the non triggered dag runs,
                                    # between start date and today
) as dag: 
  is_forex_rates_available = HttpSensor(
    task_id='is_forex_rates_available', # must be unique in this dag
    http_conn_id='forex_api',
    endpoint="marclamberti/f45f872dea4dfd3eaa015a4a1af4b39b", # after host name
    response_check=lambda response: "rates" in response.text, # if rates in response
    poke_interval=5, # check every 5 secs
    timeout=20 # if 20 secs later, still not available, then task ends in failure, should always specify it, as a best practice
  )
