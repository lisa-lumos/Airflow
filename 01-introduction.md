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
One node architecture. There are 4 components within this node: Web server, Scheduler, Metastore, Executor. 

In this architecture, the Web server fetches some metadata from the meta database of Airflow, to display information corresponding to your DAGs, your task instances, or your users in the user interface. Next, the Scheduler interacts with the meta database and th executor to trigger your DAGs. Finally, the executor interacts with the meta database to update the tasks that have been completed. 

The executor has an internal queue, which is part of the executor. This ensures the tasks are executed in the right order. 

By default, you get the sequential executor to execute your tasks, one after the other. When you scale up Airflow, you can use the local executor, where your tasks are executed in subprocesses with both executors. 

To execute as many tasks as you want, you need a different architecture - the multi-node architecture. This is usually done with Celery, which is a way to process your tasks on multiple machines. It looks like this:
- Node 1: Web server, Scheduler, Executor. 
- Node 2: Metastore, Queue
- Worker Nodes 1, 2, 3, ..., each machine holds an Airflow Worker. 

Note that in Node 2, the queue is external to the Executor. You will have Redis or RabbitMQ, so that you can spread your tasks among multiple machines. 

The process is slightly different compared with the single node architecture - The Executor pushes the tasks into the queue, 

Redis is an open source (BSD licensed), in-memory data structure store, used as a database, cache, and message broker. Once the tasks are in the queue, they are ready to be pulled by the Workers. 

What happens when a DAG is triggered. Assume you have a new DAG in your Dags folder, called "dag.py". 
1. Once the DAG is in the folder, both the Scheduler and the Web Server will parse the DAG. 
2. Then, the Scheduler will verify if the DAG is ready to be triggered. If so, a DAG object (an instance of your DAG running at a given time) is created, which is stored in the database of Airflow, with the status of "running". 
3. If there is a task ready to be triggered in the DAG, the Scheduler creates a task instance object, which is stored in the meta database as with a status of "scheduled". 
4. The Scheduler then sends the task instance object to the Executor, and its status is updated to "queued". 
5. Once the Executor is ready to run the task, the task instance will have the status of "running". When the task completes, its status is updated again. 
6. Finally, the scheduler verifies if the task is done, an if there is no more task need to execute. If so, the DAG object has the status of "completed". 
7. The Web Server updates the UI, so each time you refresh the UI, you get the latest information. 

## The little secret of the web server and the scheduler
both the Web Server and Scheduler parse your DAGs. You can configure this parsing process with different configuration settings.

With the Scheduler:
- `min_file_process_interval`. Number of seconds after which a DAG file is parsed. The DAG file is parsed every min_file_process_interval number of seconds. Updates to DAGs are reflected after this interval.
- `dag_dir_list_interval`. How often (in seconds) to scan the DAGs directory for new files. Default to 5 minutes.

Which means you have to wait up to 5 minutes before your DAG gets detected by the scheduler, and then it is parsed every 30 seconds by default.

With the Web Server:
- `worker_refresh_interval`. Number of seconds to wait before refreshing a batch of workers. 30 seconds by default. Which means every 30 seconds, the web server parses for new DAG in your DAG folder.

Remember: By default, when you add a new DAG you will have to wait up to 5 minutes before getting your DAG on the UI and then if you modify it, you will have to wait up to 30 seconds before getting your DAG updated.

## Installing Airflow




## Quick tour of Airflow UI




## Quick tour of Airflow CLI







































