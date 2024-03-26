# 2. The Forex data pipeline
## Docker intro
With Docker, you can run softwares regardless of its dependencies and the OS used. 

The dockerfile contains all the instructions needed to run your app. 

A Docker image will be built upon a dockerfile, and when you do `docker run`, you get a docker container based on that docker image, and your app runs inside that container. 

Docker Compose is based on Docker, and allows you to define/run multi-container applications. For example, with Airflow, you have 3 core components: the db, the web server and the scheduler. Each of the components will be a Docker container. 

You do not want to run everything in one single container, because if the web server fails, then you will have to restart not only the web server, but also the scheduler and the database. 

The docker compose file is a yml file, describing the services you run for your application. With this, you do not need to run docker run for each service - a single command will work. 

All 3 of the containers will share the same network, so they can communicate with each other. 

In the "docker-compose.yml" file, it specifies the postgres "dockerfile" location and container name, and the airflow "dockerfile" location and container name, etc. It also specifies the port-to-port and folder-to-folder bindings. 

## Docker performances
In docker settings, under Resources pane, make sure at least 6-8 GB of memory is allocated. Also, always make sure to update it. 

## Project: The Forex (Foreign Exchange) Data Pipeline
The Euro fluctuates against the USD. 

Flow of the Forex data pipeline:
1. Check availability of Forex rates url
2. Check the availability of the file having currencies to watch
3. Download forex rates with Python
4. Save the forex rates in HDFS
5. Create a Hive table to store forex rates from the HDFS
6. Process forex rates with Spark
7. Sent a Email notification
8. Send a Slack notification

Hive allows you to interact with the HDFS files, using SQL syntax.

Hue allows you to have a dashboard to check the data in Hive and HDFS. 

## A bit more about the architecture
skipped. 

## Definitions
### DAG
In airflow, a dag is a data pipeline. Each node in a dag is a task. The edges are dependencies between the tasks. There are no loops in a dag. 

### Operator
An operator is a task.

For example, you have a dag which contains 3 tasks
1. Execute a Python function, using PythonOperator
2. Execute a Bash command, using BashOperator
3. Execute a SQL request, using PostgresOperator

3 types of operators:
1. Action operators, allow you do execute something, like PythonOperator. 
2. Transfer operators, allow you to transfer data from source to destination, like Postgres to MYSQL operator. 
3. Sensor operators, allow you to wait for something to happen, before moving to the next task, like waiting for a file to land at a specific location in the file system. By default, it checks every 1min. 

## Define your DAG
In the folder "02-airflow-docker-files/mnt/airflow/dags", create a new file "forex_data_pipeline.py":
```py
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

```



## Check if the API is available - HttpSensor


## Check if the currency file is available - FileSensor


## Download the forex rates from the API - PythonOperator


## Save the forex rates into HDFS - BashOperator


## Create the Hive table forex_rates - HiveOperator


## Process the forex rates with Spark - SparkSubmitOperator


## Send email notifications - EmailOperator


## Send Slack notifications - SlackWebhookOperator


## Add dependencies between tasks


## The Forex Data Pipeline in action!







