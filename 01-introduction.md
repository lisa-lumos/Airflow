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
The manual setup steps:
```console
# first, make sure Docker Desktop is installed, 
# and that the app is opened and running. 

# start a Docker container, with Python 3.8 installed
# execute a bash session in the container, 
# so you can interact with it from your machine
# the port 8080 of the container is binded with the port 8080 of the machine,
# so you can reach the UI of airflow inside the Docker container
docker run -it --rm -p 8080:8080 python:3.8-slim /bin/bash

# below commands are executed inside the container: 

root@470fefdbb331:/# ls
bin   dev  home  media  opt   root  sbin  sys  usr
boot  etc  lib   mnt    proc  run   srv   tmp  var

root@470fefdbb331:/# python --version
Python 3.8.18

# export an env var, specifying where Airflow should be installed,
# and where it will generate its files/folders it needs. 
# After this, check if the var indeed exported
root@470fefdbb331:/# export AIRFLOW_HOME=/usr/local/airflow
root@470fefdbb331:/# env | grep airflow

# need below tools and dependencies before installing Airflow
root@470fefdbb331:/# apt-get update -y && apt-get install -y wget libczmq-dev curl libssl-dev git inetutils-telnet bind9utils freetds-dev libkrb5-dev libsasl2-dev libffi-dev libpq-dev freetds-bin build-essential default-libmysqlclient-dev apt-utils rsync zip unzip gcc && apt-get clean

# create a user called airflow
# whose home dir is same with the airflow env variable
# then verify this user exists
root@470fefdbb331:/# useradd -ms /bin/bash -d ${AIRFLOW_HOME} airflow
root@470fefdbb331:/# cat /etc/passwd | grep airflow
airflow:x:1000:1000::/usr/local/airflow:/bin/bash

# upgrade the pip
root@470fefdbb331:/# pip install --upgrade pip

# log in as user airflow
root@470fefdbb331:/# su - airflow

# check home folder path
airflow@470fefdbb331:~$ pwd
/usr/local/airflow

# create python venv, activate it
airflow@470fefdbb331:~$ python -m venv .sandbox
airflow@470fefdbb331:~$ source .sandbox/bin/activate

# download the constraint file, 
# that makes sure you have the right dependencies/versions
# Always install Airflow with a constraint file
(.sandbox) airflow@470fefdbb331:~$ wget https://raw.githubusercontent.com/apache/airflow/constraints-2.0.2/constraints-3.8.txt

# take a look at the constraint file
(.sandbox) airflow@470fefdbb331:~$ cat constraints-3.8.txt

# Airflow 2.0 is delivered as multiple separated, but connected packages
# For example, with the Kubernetes provider package, you can use its pod operator. 
# If you install airflow without any extras/providers,
# you will only get the Airflow Core, with limited capabilities. 
# below command installs Airflow, including some extras/providers,
# and specifies the constraint file to use
(.sandbox) airflow@470fefdbb331:~$ pip install "apache-airflow[crypto,celery,postgres,cncf.kubernetes,docker]"==2.0.2 --constraint ./constraints-3.8.txt

# generate the files/folders needed by airflow,
# and initialize its meta database
# then check to see the "airflow" folder
(.sandbox) airflow@470fefdbb331:~$ airflow db init
(.sandbox) airflow@470fefdbb331:~$ ls
airflow  constraints-3.8.txt

# see inside the airflow folder
# 1st file is airflow config file
# 2nd file is the SQLite database of airflow, used with the default sequential executor
# 3rd folder is contains logs for scheduler and tasks
# 4th file is web server config file, such as for authenticating users in the UI
airflow@470fefdbb331:~$ ls ./airflow
airflow.cfg  airflow.db  logs  webserver_config.py

# start the scheduler in the background
(.sandbox) airflow@470fefdbb331:~$ airflow scheduler &

# create an user for airflow 
# first, see the help:
(.sandbox) airflow@470fefdbb331:~$ airflow users create -h
examples:
To create an user with "Admin" role and username equals to "admin", run:

    $ airflow users create \
          --username admin \
          --firstname FIRST_NAME \
          --lastname LAST_NAME \
          --role Admin \
          --email admin@example.org
# use the above format to create user
(.sandbox) airflow@470fefdbb331:~$ airflow users create -u admin -f admin -l admin -r Admin -e admin@email.com -p admin

# start the webserver in the background
(.sandbox) airflow@470fefdbb331:~$ airflow webserver &

# Verify the webserver is working:
# go to browser, go to localhost:8080
# see the sign in page, type admin for both fields,a nd Sign in 
# Then you have access to the DAGs view

# to exit the docker container,
# hit control + D twice. 
# then airflow also stops running
```

The alternative, and the easiest and fastest way to setup and run Airflow, is by using Docker - build a Docker image, based on the below docker file, which basically contains all the commands that was run manually in the prv section. With a single `docker ...` command, you will be able to run/stop Airflow. Will need 3 files to start - find them in "01-airflow-basic-docker-image" folder. 

"Dokerfile":
```sh
# Base Image
FROM python:3.8-slim
LABEL maintainer="MarcLamberti"

# Arguments that can be set with docker build
ARG AIRFLOW_VERSION=2.0.2
ARG AIRFLOW_HOME=/opt/airflow

# Export the environment variable AIRFLOW_HOME where airflow will be installed
ENV AIRFLOW_HOME=${AIRFLOW_HOME}

# Install dependencies and tools
RUN apt-get update -yqq && \
    apt-get upgrade -yqq && \
    apt-get install -yqq --no-install-recommends \ 
    wget \
    libczmq-dev \
    curl \
    libssl-dev \
    git \
    inetutils-telnet \
    bind9utils freetds-dev \
    libkrb5-dev \
    libsasl2-dev \
    libffi-dev libpq-dev \
    freetds-bin build-essential \
    default-libmysqlclient-dev \
    apt-utils \
    rsync \
    zip \
    unzip \
    gcc \
    vim \
    locales \
    && apt-get clean

COPY ./constraints-3.8.txt /constraints-3.8.txt

# Upgrade pip
# Create airflow user 
# Install apache airflow with subpackages
RUN pip install --upgrade pip && \
    useradd -ms /bin/bash -d ${AIRFLOW_HOME} airflow && \
    pip install apache-airflow[postgres]==${AIRFLOW_VERSION} --constraint /constraints-3.8.txt

# Copy the entrypoint.sh from host to container (at path AIRFLOW_HOME)
COPY ./entrypoint.sh ./entrypoint.sh

# Set the entrypoint.sh file to be executable
RUN chmod +x ./entrypoint.sh

# Set the owner of the files in AIRFLOW_HOME to the user airflow
RUN chown -R airflow: ${AIRFLOW_HOME}

# Set the username to use
USER airflow

# Set workdir (it's like a cd inside the container)
WORKDIR ${AIRFLOW_HOME}

# Create the dags folder which will contain the DAGs
RUN mkdir dags

# Expose ports (just to indicate that this container needs to map port)
EXPOSE 8080

# Execute the entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]

```

"constraints-3.8.txt". 

"entrypoint.sh":
```sh
#!/usr/bin/env bash

# Initiliase the metastore
airflow db init

# Run the scheduler in background
airflow scheduler &> /dev/null &

# Create user
airflow users create -u admin -p admin -r Admin -e admin@admin.com -f admin -l admin

# Run the web server in foreground (for docker logs)
exec airflow webserver

```

Commands:
```console
# navigate to the folder that has the above 3 files
# build the Docker image, named "airflow-basic"
lisa@mac16 ~/Desktop> cd airflow-docker/
lisa@mac16 ~/D/airflow-docker> ls
Dockerfile  constraints-3.8.txt  entrypoint.sh
lisa@mac16 ~/D/airflow-docker> docker build -t airflow-basic .

# should see the first docker image named "airflow-basic"
lisa@mac16 ~/D/airflow-docker> docker image ls
REPOSITORY                      TAG        IMAGE ID       CREATED         SIZE
airflow-basic                   latest     e78a934d2f72   2 minutes ago   1.13GB
python                          3.8-slim   054df0836f52   3 weeks ago     154MB
cart                            latest     ee4954f2a68d   16 months ago   301MB
readitacrlisa.azurecr.io/cart   latest     ee4954f2a68d   16 months ago   301MB

# run the container
# -d means run it in the background
lisa@mac16 ~/D/airflow-docker> docker run --rm -d -p 8080:8080 airflow-basic

# verify if the Docker container is running
lisa@mac16 ~/D/airflow-docker> docker ps
CONTAINER ID   IMAGE           COMMAND            CREATED          STATUS          PORTS                    NAMES
7e99f8163618   airflow-basic   "/entrypoint.sh"   44 seconds ago   Up 44 seconds   0.0.0.0:8080->8080/tcp   eager_diffie

# Verify the webserver is working:
# go to browser, go to localhost:8080
# see the sign in page, type admin for both fields,a nd Sign in 
# Then you have access to the DAGs view

```

## Quick tour of Airflow UI
The DAGs view let you see all of the DAGs in your folder "dags". 

For each DAG in the list, you can toggle to pause/unpause it. Note that the DAG need to be in Unpaused state to be available for scheduling/manual-triggers. 

Each DAG can have tags. It is highly recommended to add tags to DAGs. Because then you can "Filter DAGs by tag" in the UI. 

Each DAG has an owner. At the top pane, Browse -> Audit Logs, it would give you auditing information, for each user. 

For each DAG, you can see its run history, and their status (success/running/failed). 

Each DAG has a Schedule column. 

Also, for each DAG, you can get the status of the tasks that are getting executed in the current active DAG runs. 

Deleting a DAG in the UI will only delete its meta data, will not delete the code file. 

The refresh button no longer works with Airflow 2.0. 

Under "Links" column, you can access the code of the DAG, it details, etc. 

When you click on a DAG in the UI, it opens the Tree View of it. You can see the status (queued/running/success/failed/...) of all the tasks that have been, or being executed. 

When you go to the Graph View, you can task dependencies. By hovering over each task, you can see which Operator that task is based on. You can toggle "Auto-refresh" to see each task's color automatically change as the DAG runs. When you click on a node, you will see the context menu, where you can take actions to your task, for example, checking it logs, inject data at runtime, see all the task instances for this task, running this task ignoring all dependencies, clearing a task so it is ready for retry, marking the task as failed to check the behavior of tasks, 

The "Grantt" view shows how long each task took to run, and in which order. It is useful to identify bottlenecks. This chart can also be used to verify if you tasks are able to run in parallel. 

The "Code" view. Can be used to make sure the modifications you made to your DAG has been applied to your airflow instance. 

## Quick tour of Airflow CLI
With the cli, you can interact with a lot of things, such as you DAGs, task instances, diagrams, etc. 

For some commands, you have to used the cli to execute them - you cannot do it from the UI. For example, if you want to backfill your DAG, trigger all the non-triggered diagrams, even if the backfilling process is disabled. 

```console
lisa@mac16 ~/D/airflow-docker> docker ps
CONTAINER ID   IMAGE           COMMAND            CREATED      STATUS      PORTS                    NAMES
7e99f8163618   airflow-basic   "/entrypoint.sh"   8 days ago   Up 8 days   0.0.0.0:8080->8080/tcp   eager_diffie

# open a bsh session inside the Docker container of Airflow
lisa@mac16 ~/D/airflow-docker> docker exec -it 7e99f8163618 /bin/bash 

# see helps
# note that airflow commands are grouped
# depends on the resource you want to interact with
airflow@7e99f8163618:~$ airflow -h

# initialize the metadata base, generate needed files/folders for Airflow
airflow@7e99f8163618:~$ airflow db init

# The "airflow db reset" cmd deletes all metadata. Should never use it in prod. 
# The "airflow db upgrade" cmd updates the airflow version.  

# The "airflow webserver" starts the airflow webserver.  
# The "airflow scheduler" starts the airflow scheduler.  
# The "airflow celery worker" declares this machine as an airflow worker, start it.  

# list every DAG, show its path, owner, and paused status
# useful if you created a new DAG, and confirm whether airflow is aware of it. 
airflow@7e99f8163618:~$ airflow dags list

# trigger a dag run for a particular date
airflow@7e99f8163618:~$ airflow dags trigger example_bash_operator -e 2024-03-08

# see run history of a dag
airflow@7e99f8163618:~$ airflow dags list-runs -d example_bash_operator

# can be used to execute all the non-trigger dag runs between a time span specified. 
# the --reset-dagruns will force the already triggered dags in the past to re-run
airflow@7e99f8163618:~$ airflow dags backfill

# list all the tasks in a dag
# use case: you added a new task in an existing DAG, and
#           you need to make sure Airflow is aware of it. 
airflow@7e99f8163618:~$ airflow tasks list example_bash_operator

# Best practice: 
# Each time you add a new task to your dag,
# make sure that the task works, with this command. 
# This will run a task without checking for dependencies,
# nor recording its state in the database. 
# the parameters are: dag name, task name, run date
airflow@7e99f8163618:~$ airflow tasks test example_bash_operator runme_0 2024-03-07

# exit from the container
airflow@7e99f8163618:~$ exit

# Stop the Airflow docker container
lisa@mac16 ~/D/airflow-docker> docker stop 7e99f8163618

```
