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

"constraints-3.8.txt":
```
# Editable install with no version control (apache-airflow==2.0.2)
APScheduler==3.6.3
Authlib==0.15.3
Babel==2.9.0
Flask-AppBuilder==3.2.3
Flask-Babel==1.0.0
Flask-Bcrypt==0.7.1
Flask-Caching==1.10.1
Flask-JWT-Extended==3.25.1
Flask-Login==0.4.1
Flask-OAuthlib==0.9.5
Flask-OpenID==1.2.5
Flask-SQLAlchemy==2.5.1
Flask-WTF==0.14.3
Flask==1.1.2
GitPython==3.1.15
HeapDict==1.0.1
JPype1==1.2.1
JayDeBeApi==1.2.3
Jinja2==2.11.3
Mako==1.1.4
Markdown==3.3.4
MarkupSafe==1.1.1
PyHive==0.6.3
PyJWT==1.7.1
PyNaCl==1.4.0
PySmbClient==0.1.5
PyYAML==5.4.1
Pygments==2.8.1
SQLAlchemy-JSONField==1.0.0
SQLAlchemy-Utils==0.37.0
SQLAlchemy==1.3.24
Sphinx==3.4.3
Unidecode==1.2.0
WTForms==2.3.3
Werkzeug==1.0.1
adal==1.2.7
aiohttp==3.7.4.post0
alabaster==0.7.12
alembic==1.5.8
amqp==2.6.1
analytics-python==1.2.9
ansiwrap==0.8.4
apache-airflow-providers-airbyte==1.0.0
apache-airflow-providers-amazon==1.3.0
apache-airflow-providers-apache-beam==1.0.1
apache-airflow-providers-apache-cassandra==1.0.1
apache-airflow-providers-apache-druid==1.1.0
apache-airflow-providers-apache-hdfs==1.0.1
apache-airflow-providers-apache-hive==1.0.3
apache-airflow-providers-apache-kylin==1.0.1
apache-airflow-providers-apache-livy==1.1.0
apache-airflow-providers-apache-pig==1.0.1
apache-airflow-providers-apache-pinot==1.0.1
apache-airflow-providers-apache-spark==1.0.2
apache-airflow-providers-apache-sqoop==1.0.1
apache-airflow-providers-celery==1.0.1
apache-airflow-providers-cloudant==1.0.1
apache-airflow-providers-cncf-kubernetes==1.1.0
apache-airflow-providers-databricks==1.0.1
apache-airflow-providers-datadog==1.0.1
apache-airflow-providers-dingding==1.0.2
apache-airflow-providers-discord==1.0.1
apache-airflow-providers-docker==1.1.0
apache-airflow-providers-elasticsearch==1.0.3
apache-airflow-providers-exasol==1.1.1
apache-airflow-providers-facebook==1.1.0
apache-airflow-providers-ftp==1.0.1
apache-airflow-providers-google==2.2.0
apache-airflow-providers-grpc==1.1.0
apache-airflow-providers-hashicorp==1.0.2
apache-airflow-providers-http==1.1.1
apache-airflow-providers-imap==1.0.1
apache-airflow-providers-jdbc==1.0.1
apache-airflow-providers-jenkins==1.1.0
apache-airflow-providers-jira==1.0.1
apache-airflow-providers-microsoft-azure==1.3.0
apache-airflow-providers-microsoft-mssql==1.0.1
apache-airflow-providers-microsoft-winrm==1.1.0
apache-airflow-providers-mongo==1.0.1
apache-airflow-providers-mysql==1.1.0
apache-airflow-providers-neo4j==1.0.1
apache-airflow-providers-odbc==1.0.1
apache-airflow-providers-openfaas==1.1.1
apache-airflow-providers-opsgenie==1.0.2
apache-airflow-providers-oracle==1.1.0
apache-airflow-providers-pagerduty==1.0.1
apache-airflow-providers-papermill==1.0.2
apache-airflow-providers-plexus==1.0.1
apache-airflow-providers-postgres==1.0.1
apache-airflow-providers-presto==1.0.2
apache-airflow-providers-qubole==1.0.2
apache-airflow-providers-redis==1.0.1
apache-airflow-providers-salesforce==2.0.0
apache-airflow-providers-samba==1.0.1
apache-airflow-providers-segment==1.0.1
apache-airflow-providers-sendgrid==1.0.2
apache-airflow-providers-sftp==1.1.1
apache-airflow-providers-singularity==1.1.0
apache-airflow-providers-slack==3.0.0
apache-airflow-providers-snowflake==1.2.0
apache-airflow-providers-sqlite==1.0.2
apache-airflow-providers-ssh==1.3.0
apache-airflow-providers-tableau==1.0.0
apache-airflow-providers-telegram==1.0.2
apache-airflow-providers-trino==1.0.0
apache-airflow-providers-vertica==1.0.1
apache-airflow-providers-yandex==1.0.1
apache-airflow-providers-zendesk==1.0.1
apache-beam==2.28.0
apipkg==1.5
apispec==3.3.2
appdirs==1.4.4
argcomplete==1.12.3
arrow==1.0.3
asn1crypto==1.4.0
astroid==2.5.3
async-generator==1.10
async-timeout==3.0.1
atlasclient==1.0.0
attrs==20.3.0
avro-python3==1.9.2.1
aws-xray-sdk==2.7.0
azure-batch==10.0.0
azure-common==1.1.27
azure-core==1.13.0
azure-cosmos==3.2.0
azure-datalake-store==0.0.52
azure-identity==1.5.0
azure-keyvault-certificates==4.2.1
azure-keyvault-keys==4.3.1
azure-keyvault-secrets==4.2.0
azure-keyvault==4.1.0
azure-kusto-data==0.0.45
azure-mgmt-containerinstance==1.5.0
azure-mgmt-core==1.2.2
azure-mgmt-datafactory==1.1.0
azure-mgmt-datalake-nspkg==3.0.1
azure-mgmt-datalake-store==0.5.0
azure-mgmt-nspkg==3.0.2
azure-mgmt-resource==16.1.0
azure-nspkg==3.0.2
azure-storage-blob==12.8.0
azure-storage-common==2.1.0
azure-storage-file==2.1.0
backcall==0.2.0
bcrypt==3.2.0
beautifulsoup4==4.7.1
billiard==3.6.4.0
black==20.8b1
blinker==1.4
boto3==1.17.54
boto==2.49.0
botocore==1.20.54
bowler==0.9.0
cached-property==1.5.2
cachetools==4.2.1
cassandra-driver==3.20.2
cattrs==1.5.0
celery==4.4.7
certifi==2020.12.5
cffi==1.14.5
cfgv==3.2.0
cgroupspy==0.1.6
chardet==3.0.4
click==7.1.2
clickclick==20.10.2
cloudant==2.14.0
cloudpickle==1.4.1
colorama==0.4.4
colorlog==5.0.1
commonmark==0.9.1
connexion==2.7.0
coverage==5.5
crcmod==1.7
croniter==0.3.37
cryptography==3.4.7
curlify==2.2.1
cx-Oracle==8.1.0
dask==2021.4.0
datadog==0.41.0
decorator==5.0.7
defusedxml==0.7.1
dill==0.3.2
distlib==0.3.1
distributed==2.19.0
dnspython==1.16.0
docker-pycreds==0.4.0
docker==3.7.3
docopt==0.6.2
docutils==0.17.1
ecdsa==0.14.1
elasticsearch-dbapi==0.1.0
elasticsearch-dsl==7.3.0
elasticsearch==7.5.1
email-validator==1.1.2
entrypoints==0.3
eventlet==0.30.2
execnet==1.8.0
facebook-business==10.0.0
fastavro==1.4.0
fasteners==0.16
filelock==3.0.12
fissix==20.8.0
flake8-colors==0.1.9
flake8==3.9.1
flaky==3.7.0
flower==0.9.7
freezegun==1.1.0
fsspec==2021.4.0
future==0.18.2
gcsfs==0.8.0
gevent==21.1.2
gitdb==4.0.7
github3.py==2.0.0
google-ads==7.0.0
google-api-core==1.26.3
google-api-python-client==1.12.8
google-apitools==0.5.31
google-auth-httplib2==0.1.0
google-auth-oauthlib==0.4.4
google-auth==1.29.0
google-cloud-automl==2.3.0
google-cloud-bigquery-datatransfer==3.1.1
google-cloud-bigquery-storage==2.4.0
google-cloud-bigquery==1.28.0
google-cloud-bigtable==1.7.0
google-cloud-build==2.0.0
google-cloud-container==1.0.1
google-cloud-core==1.6.0
google-cloud-datacatalog==3.1.1
google-cloud-dataproc==2.3.1
google-cloud-datastore==1.15.3
google-cloud-dlp==1.0.0
google-cloud-kms==2.2.0
google-cloud-language==1.3.0
google-cloud-logging==2.3.1
google-cloud-memcache==0.3.0
google-cloud-monitoring==2.2.1
google-cloud-os-login==2.1.0
google-cloud-pubsub==2.4.1
google-cloud-redis==2.1.0
google-cloud-secret-manager==1.0.0
google-cloud-spanner==1.19.1
google-cloud-speech==1.3.2
google-cloud-storage==1.37.1
google-cloud-tasks==2.2.0
google-cloud-texttospeech==1.0.1
google-cloud-translate==1.7.0
google-cloud-videointelligence==1.16.1
google-cloud-vision==1.0.0
google-cloud-workflows==0.2.0
google-crc32c==1.1.2
google-resumable-media==1.2.0
googleapis-common-protos==1.53.0
graphviz==0.16
greenlet==1.0.0
grpc-google-iam-v1==0.12.3
grpcio-gcp==0.2.2
grpcio==1.37.0
gunicorn==19.10.0
hdfs==2.6.0
hmsclient==0.1.1
httplib2==0.17.4
humanize==3.4.1
hvac==0.10.9
identify==2.2.4
idna==2.10
imagesize==1.2.0
importlib-metadata==1.7.0
importlib-resources==1.5.0
inflection==0.5.1
iniconfig==1.1.1
ipdb==0.13.7
ipython-genutils==0.2.0
ipython==7.22.0
iso8601==0.1.14
isodate==0.6.0
isort==5.8.0
itsdangerous==1.1.0
jedi==0.18.0
jira==2.0.0
jmespath==0.10.0
json-merge-patch==0.2
jsondiff==1.3.0
jsonpath-ng==1.5.2
jsonschema==3.2.0
jupyter-client==6.1.12
jupyter-core==4.7.1
jwcrypto==0.8
kombu==4.6.11
kubernetes==11.0.0
kylinpy==2.8.4
lazy-object-proxy==1.4.3
ldap3==2.9
libcst==0.3.18
locket==0.2.1
lockfile==0.12.2
marshmallow-enum==1.5.1
marshmallow-oneofschema==2.1.0
marshmallow-sqlalchemy==0.23.1
marshmallow==3.11.1
mccabe==0.6.1
mock==2.0.0
mongomock==3.22.1
more-itertools==8.7.0
moreorless==0.4.0
moto==2.0.5
msal-extensions==0.3.0
msal==1.11.0
msgpack==1.0.2
msrest==0.6.21
msrestazure==0.6.4
multi-key-dict==2.0.3
multidict==5.1.0
mypy-extensions==0.4.3
mypy==0.770
mysql-connector-python==8.0.22
mysqlclient==2.0.3
natsort==7.1.1
nbclient==0.5.3
nbformat==5.1.3
neo4j==4.2.1
nest-asyncio==1.5.1
nodeenv==1.6.0
nteract-scrapbook==0.4.2
ntlm-auth==1.5.0
numpy==1.20.2
oauth2client==4.1.3
oauthlib==2.1.0
openapi-schema-validator==0.1.5
openapi-spec-validator==0.3.0
oscrypto==1.2.1
packaging==20.9
pandas-gbq==0.14.1
pandas==1.2.4
papermill==2.3.3
parameterized==0.8.1
paramiko==2.7.2
parso==0.8.2
partd==1.2.0
pathspec==0.8.1
pbr==5.5.1
pdpyras==4.1.4
pendulum==2.1.2
pexpect==4.8.0
pickleshare==0.7.5
pinotdb==0.3.3
pipdeptree==2.0.0
pluggy==0.13.1
ply==3.11
plyvel==1.3.0
portalocker==1.7.1
pre-commit==2.12.1
presto-python-client==0.7.0
prison==0.1.3
prometheus-client==0.8.0
prompt-toolkit==3.0.18
proto-plus==1.18.1
protobuf==3.15.8
psutil==5.8.0
psycopg2-binary==2.8.6
ptyprocess==0.7.0
py4j==0.10.9
py==1.10.0
pyOpenSSL==19.1.0
pyarrow==2.0.0
pyasn1-modules==0.2.8
pyasn1==0.4.8
pycodestyle==2.7.0
pycountry==20.7.3
pycparser==2.20
pycryptodomex==3.10.1
pydata-google-auth==1.1.0
pydot==1.4.2
pydruid==0.6.2
pyenchant==3.2.0
pyexasol==0.18.1
pyflakes==2.3.1
pykerberos==1.2.1
pylint==2.7.4
pymongo==3.11.3
pymssql==2.2.1
pyodbc==4.0.30
pyparsing==2.4.7
pyrsistent==0.17.3
pysftp==0.2.9
pyspark==3.1.1
pytest-cov==2.11.1
pytest-forked==1.3.0
pytest-instafail==0.4.2
pytest-rerunfailures==9.1.1
pytest-timeouts==1.2.1
pytest-xdist==2.2.1
pytest==6.2.3
python-daemon==2.3.0
python-dateutil==2.8.1
python-editor==1.0.4
python-http-client==3.3.2
python-jenkins==1.7.0
python-jose==3.2.0
python-ldap==3.3.1
python-nvd3==0.15.0
python-slugify==4.0.1
python-telegram-bot==13.0
python3-openid==3.2.0
pytz==2021.1
pytzdata==2020.1
pywinrm==0.4.1
pyzmq==22.0.3
qds-sdk==1.16.1
redis==3.5.3
regex==2021.4.4
requests-kerberos==0.12.0
requests-mock==1.8.0
requests-ntlm==1.1.0
requests-oauthlib==1.1.0
requests-toolbelt==0.9.1
requests==2.25.1
responses==0.13.2
rich==9.2.0
rsa==4.7.2
s3transfer==0.4.0
sasl==0.2.1
semver==2.13.0
sendgrid==6.6.0
sentinels==1.0.0
sentry-sdk==1.0.0
setproctitle==1.2.2
simple-salesforce==1.11.1
six==1.15.0
slack-sdk==3.5.0
smmap==4.0.0
snakebite-py3==3.0.5
snowballstemmer==2.1.0
snowflake-connector-python==2.4.2
snowflake-sqlalchemy==1.2.4
sortedcontainers==2.3.0
soupsieve==2.2.1
sphinx-airflow-theme==0.0.2
sphinx-argparse==0.2.5
sphinx-autoapi==1.0.0
sphinx-copybutton==0.3.1
sphinx-jinja==1.1.1
sphinx-rtd-theme==0.5.2
sphinxcontrib-applehelp==1.0.2
sphinxcontrib-devhelp==1.0.2
sphinxcontrib-dotnetdomain==0.4
sphinxcontrib-golangdomain==0.2.0.dev0
sphinxcontrib-htmlhelp==1.0.3
sphinxcontrib-httpdomain==1.7.0
sphinxcontrib-jsmath==1.0.1
sphinxcontrib-qthelp==1.0.3
sphinxcontrib-redoc==1.6.0
sphinxcontrib-serializinghtml==1.1.4
sphinxcontrib-spelling==5.2.1
spython==0.1.13
sshtunnel==0.1.5
starkbank-ecdsa==1.1.0
statsd==3.3.0
swagger-ui-bundle==0.0.8
tableauserverclient==0.15.0
tabulate==0.8.9
tblib==1.7.0
tenacity==6.2.0
termcolor==1.1.0
text-unidecode==1.3
textwrap3==0.9.2
thrift-sasl==0.4.2
thrift==0.13.0
toml==0.10.2
toolz==0.11.1
tornado==6.1
tqdm==4.60.0
traitlets==5.0.5
trino==0.305.0
typed-ast==1.4.3
typing-extensions==3.7.4.3
typing-inspect==0.6.0
tzlocal==2.1
ujson==4.0.2
unicodecsv==0.14.1
uritemplate==3.0.1
urllib3==1.25.11
vertica-python==1.0.1
vine==1.3.0
virtualenv==20.4.4
volatile==2.1.0
watchtower==0.7.3
wcwidth==0.2.5
websocket-client==0.58.0
wrapt==1.12.1
xmltodict==0.12.0
yamllint==1.26.1
yandexcloud==0.81.0
yarl==1.6.3
zdesk==2.7.1
zict==2.0.0
zipp==3.4.1
zope.event==4.5.0
zope.interface==5.4.0

```

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




## Quick tour of Airflow CLI







































