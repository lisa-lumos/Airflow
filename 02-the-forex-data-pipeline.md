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
from airflow.sensors.http_sensor import HttpSensor
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.apache.hive.operators.hive import HiveOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.email import EmailOperator
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator


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


def _get_message() -> str:
    return "Hi from forex_data_pipeline"

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

    # create a table on top of the file, with Hive
    # to be able to query it, using hql (like sql)
    # documentation -> Providers packages -> Apache Hive -> Python API
    # -> airflow.providers.apache.hive.operators.hive
    # to check for tables, go to Hue, and default -> refresh
    # to query it, go to Editor, run "select * from forex_rates"
    # This step creates an empty table in Hive. 
    creating_forex_rates_table = HiveOperator(
        task_id="creating_forex_rates_table",
        hive_cli_conn_id="hive_conn",
        hql="""
            CREATE EXTERNAL TABLE IF NOT EXISTS forex_rates(
                base STRING,
                last_update DATE,
                eur DOUBLE,
                usd DOUBLE,
                nzd DOUBLE,
                gbp DOUBLE,
                jpy DOUBLE,
                cad DOUBLE
                )
            ROW FORMAT DELIMITED
            FIELDS TERMINATED BY ','
            STORED AS TEXTFILE
        """
    )

    # Airflow is an orchestrator, not a processing framework, 
    # so you should not process TBs of data in Airflow.
    # Instead, you should trigger a Spark job,
    # where the processing of TBs of data is done. 
    # documentation -> Providers packages -> Apache Spark -> Python API
    # -> airflow.providers.apache.spark.operators.spark_submit
    # After testing this task, should see the table now have 2 rows
    forex_processing = SparkSubmitOperator(
        task_id="forex_processing",
        application="/opt/airflow/dags/scripts/forex_processing.py", # the path of the python file that Spark need to execute
        conn_id="spark_conn",
        verbose=False # avoid excessive logs
    )

    # you need to first configure your email provider,
    # to be able to send an email from the data pipeline,
    # by using your email address. 
    # For GMail, this url: https://security.google.com/settings/security/apppasswords
    # Give an app name, such as "airflow", 
    # then get the app pwd: ryxh kqla abzl pzgy
    # then, go to "mnt/airflow/dags/airflow.cfg" to update config for airflow
    # search for "smtp", and update the settings. 

    # send_email_notification = EmailOperator(
    #     task_id="send_email_notification",
    #     to="your-receipient-email@gmail.com", # the recipient email address
    #     subject="forex_data_pipeline",
    #     html_content="<h3>forex_data_pipeline</h3>"
    # )


    # send_slack_notification = SlackWebhookOperator(
    #     task_id="send_slack_notification",
    #     http_conn_id="slack_conn",
    #     message=_get_message(),
    #     channel="#monitoring"
    # )

    # one way to set dependencies
    # is_forex_rates_available.set_downstream(is_forex_currencies_file_available)
    # is_forex_currencies_file_available.set_upstream(is_forex_rates_available)

    # cleaner way to set dependencies
    # but if the task chain is long, can break into several lines
    is_forex_rates_available >> is_forex_currencies_file_available >> downloading_rates >> saving_rates 
    saving_rates >> creating_forex_rates_table >> forex_processing
    # forex_processing >> send_email_notification >> send_slack_notification 

```

Navigate to "02-airflow-docker-files" folder, 
```console
# takes a while for first time
./start.sh

# make sure all containers show healthy
docker ps
CONTAINER ID   IMAGE                                    COMMAND                  CREATED         STATUS                   PORTS                                                                         NAMES
5b9dc58e836d   02-airflow-docker-files-hue              "./entrypoint.sh ./s…"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:32762->8888/tcp                                                       hue
45b03324f6f5   02-airflow-docker-files-hive-webhcat     "./entrypoint.sh ./s…"   2 minutes ago   Up 2 minutes (healthy)   10000-10002/tcp, 50111/tcp                                                    hive-webhcat
c2d0aae51cb8   02-airflow-docker-files-hive-server      "./entrypoint.sh ./s…"   2 minutes ago   Up 2 minutes (healthy)   10001/tcp, 0.0.0.0:32760->10000/tcp, 0.0.0.0:32759->10002/tcp                 hive-server
9931cb19c200   02-airflow-docker-files-livy             "./entrypoint"           2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:32758->8998/tcp                                                       livy
e8631e3291ef   02-airflow-docker-files-hive-metastore   "./entrypoint.sh ./s…"   2 minutes ago   Up 2 minutes (healthy)   10000-10002/tcp, 0.0.0.0:32761->9083/tcp                                      hive-metastore
7aad3af3036c   02-airflow-docker-files-spark-worker     "./entrypoint.sh ./s…"   2 minutes ago   Up 2 minutes (healthy)   10000-10002/tcp, 0.0.0.0:32764->8081/tcp                                      02-airflow-docker-files-spark-worker-1
45e5e1b15283   02-airflow-docker-files-datanode         "./entrypoint.sh ./s…"   2 minutes ago   Up 2 minutes (healthy)   9864/tcp                                                                      datanode
2125a82cd267   02-airflow-docker-files-postgres         "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:32769->5432/tcp                                                       postgres
498068701c6d   02-airflow-docker-files-spark-master     "./entrypoint.sh ./s…"   2 minutes ago   Up 2 minutes (healthy)   6066/tcp, 10000-10002/tcp, 0.0.0.0:32765->7077/tcp, 0.0.0.0:32766->8082/tcp   spark-master
d982e1fe3227   02-airflow-docker-files-namenode         "./entrypoint.sh ./s…"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:32763->9870/tcp                                                       namenode
681b9e46e905   02-airflow-docker-files-airflow          "./entrypoint.sh ./s…"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:8080->8080/tcp, 10000-10002/tcp                                       airflow
2c48698f7db6   wodby/adminer:latest                     "/entrypoint.sh php …"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:32767->9000/tcp                                                       adminer
```

Then, go to `http://localhost:8080/` in the browser, and use airflow as both username and pwd to login. 

Create the http connection. In the UI, Admin -> Connections -> + -> Conn Id: (same with defined in the task in the dag) forex_api; Conn Type: HTTP; Host: https://gist.github.com/ -> Save. 

Create the file connection. In the UI, Admin -> Connections -> + -> Conn Id: (same with defined in the task in the dag) forex_path; Conn Type: File (path); Extra: {"path": "/opt/airflow/dags/files"} -> Save. 

Create the Hive connection. In the UI, Admin -> Connections -> + -> Conn Id: (same with defined in the task in the dag) hive_conn; Conn Type: Hive Server 2 Thrift; Host: hive-server; Login: hive; Password: hive; Port: 10000 -> Save. 

Create the Spark connection. In the UI, Admin -> Connections -> + -> Conn Id: (same with defined in the task in the dag) spark_conn; Conn Type: Spark; Host: spark://spark-master; Port: 7077 -> Save. 

The smtp part of the airflow config file looks like this, with `smtp_user` and `smtp_mail_from` all set as your email address, and `smtp_password` set as the app key generated from the previous url:
```cfg
[smtp]

# If you want airflow to send emails on retries, failure, and you want to use
# the airflow.utils.email.send_email_smtp function, you have to configure an
# smtp server here
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = your-email@gmail.com
smtp_password = 1234123412341234
smtp_port = 587
smtp_mail_from = your-email@gmail.com
smtp_timeout = 30
smtp_retry_limit = 5
```

After changing the airflow config file, need to restart airflow using `docker-compose restart airflow`. 

To sent a Slack message from an Airflow task, go to "slack.com" -> Create a new workspace -> Create a Workspace -> team name: Airflow test -> (channel name that will receive notifications) airflow-monitoring -> Skip this step (the adding teammates step) -> use Slack in your browser. 

Next, to set up an application, go to "api.slack.com/apps" -> Create an App -> App Name: Airflow (the name under which the slack notifications will be sent); Development Slack Workspace: Airflow test -> Create App -> Incoming Webhooks -> Active Incoming Webhooks (toggle it on) -> Add New Webhook to Workspace -> Where should airflow post: airflow-monitoring (the channel name to receive notifications) -> Allow -> Copy the Webhook URL. It looks like "https://hooks.slack.com/services/..."

Create the Slack connection. In the UI, Admin -> Connections -> + -> Conn Id: (same with defined in the task in the dag) slack_conn; Conn Type: HTTP; Password: (the slack url, looks like https://hooks.slack.com/services/...) -> Save. 

In the command line, test all the tasks: 
```console
# copy the container id of airflow from below
docker ps

# run the bash session in the airflow container
docker exec -it 681b9e46e905 /bin/bash

# test the first task in the dag before running the dag
# should see "Marking task as SUCCESS"
# always test the tasks in a dag before running the dag
airflow tasks test forex_data_pipeline is_forex_rates_available 2024-01-01
...
[2024-03-26 03:47:08,656] {http.py:140} INFO - Sending 'GET' to url: https://gist.github.com/marclamberti/f45f872dea4dfd3eaa015a4a1af4b39b
[2024-03-26 03:47:09,264] {base.py:248} INFO - Success criteria met. Exiting.
[2024-03-26 03:47:09,274] {taskinstance.py:1219} INFO - Marking task as SUCCESS. dag_id=forex_data_pipeline, task_id=is_forex_rates_available, execution_date=20240101T000000, start_date=20240326T034612, end_date=20240326T034709

airflow tasks test forex_data_pipeline is_forex_currencies_file_available 2024-01-01

airflow tasks test forex_data_pipeline downloading_rates 2024-01-01

airflow tasks test forex_data_pipeline saving_rates 2024-01-01

airflow tasks test forex_data_pipeline creating_forex_rates_table 2024-01-01

airflow tasks test forex_data_pipeline forex_processing 2024-01-01

airflow tasks test forex_data_pipeline send_email_notification 2024-01-01

airflow tasks test forex_data_pipeline send_slack_notification 2024-01-01
```

After setting dependencies, go to the UI -> DAGs -> forex_date_pipeline -> Graph View, and see the graph. 

To trigger the dag, clean up the files that are generated by the task testings first, such as "forex_rates.json"; in Hue, execute "drop table forex_rates"; 

In the DAGs page, turn on the toggle before the "forex_data_pipeline", to turn on the dag. It will start to run immediately. 
