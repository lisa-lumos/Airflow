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

## What is a DAG (Directed Acyclic Graph)?
In airflow, a dag is a data pipeline. Each node in a dag is a task. The edges are dependencies between the tasks. There are no loops in a dag. 

## [Practice] Define your DAG


## What is an Operator?


## [Practice] Check if the API is available - HttpSensor


## [Practice] Check if the currency file is available - FileSensor


## [Practice] Download the forex rates from the API - PythonOperator


## [Practice] Save the forex rates into HDFS - BashOperator


## [Practice] Create the Hive table forex_rates - HiveOperator


## [Practice] Process the forex rates with Spark - SparkSubmitOperator


## [Practice] Send email notifications - EmailOperator


## [Practice] Send Slack notifications - SlackWebhookOperator


## [Practice] Add dependencies between tasks


## [Practice] The Forex Data Pipeline in action!







