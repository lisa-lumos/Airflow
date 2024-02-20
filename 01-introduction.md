# 1. Introduction of Apache Airflow
## Why Airflow?
1. To make sure that your data pipelines run at a given time. 
2. To author/manage/monitor your data pipelines with ease

Assume a data pipeline has 3 components. It first fetches data from an API, then it processes data using Spark, then it load the data into the database. Any link in this process could go wrong. And assume you have many many of such data pipelines. 

## What is Airflow?
An open source platform to programmatically author schedule and monitor workflows. 

Benefits:
- Dynamic. Everything is coded in Python. As long as you know Python, you are good to go. 
- Able to dynamically create tasks and data pipelines at the same time. 
- Scalable. Can execute as many tasks as you want, as long as you have enough resources for it. Has different options, such as Kubernetes executor to run air flow in Kubernetes; the Celery executer to run it on a Celery Cluster; the local executor to run it on a local machine. 
- The UI for easy monitoring. 
- Extensible. You won't be locked with Airflow. You can create your own operator/plugin for a tool, then add it to airflow. Can customize the UI, functionalities, etc. 

Core components:
- Web server. Flask server, with Gunicorn serving the UI
- Scheduler. Daemon in charge of scheduling workflows. Typically in production, you have at least 2 schedulers, for availability purposes. 
- Metastore. Database where metadata are stored. So you need a SQL database to run Airflow
- Trigger. Manage deferrable operators. A deferrable operator is a task that can suspend/resume itself. 
- Executor. Class defining how your tasks should be executed. 
- Worker. Process/sub-process executing your task. 

Note that the Executor doesn't execute your task - the Worker does. 

A task is an Operator. It encapsulates the logic that you need to achieve in this task. 
- Action operators: Execute a Python function with the Python Operator, a bash script with the bash operator, a SQL request with the Postgres operator. 
- Transfer operators: to transfer data from source A to B. 
- Sensor operators: wait for an event to happen before executing a next task. Such as waiting for an entry in your database, for a file to land in a specific location, etc. 
- Deferrable operators.

As soon you trigger your task, that task becomes a task instance. So it is an instance of an operator, with a specific date. 

A workflow is a data pipeline, which is a DAG in Airflow. 

Airflow is NOT a data streaming solution, nor a data processing framework. If you need to process your data, don't use Airflow. Airflow should be used as a trigger. 

Typically, you have spark to process your data, and you use airflow to trigger the spark job that processes your data, but you don't process your data in airflow. 

## How Airflow works?




## The little secret of the webserver and the scheduler




## Installing Airflow




## Quick tour of Airflow UI




## Quick tour of Airflow CLI







































