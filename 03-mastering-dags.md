# 3. Mastering your dags
## Start_date and schedule_interval parameters
`start_date`: The from date (at midnight) that your DAG tasks can be scheduled/triggered. It is defined with a datetime object, like `datetime.datetime(2024, 03, 28)`. This date can be in the past or in the future. Best practice: do not use dynamic values such as datetime.now(). Best practice: define the the start_date at the DAG level only (the global one). 

`schedule_interval`: The interval of time from the min(start_date at dag and task level) that your DAG will be triggered. Best practice, use cron expressions to define `scheduling_interval`, do not use timedelta objects. Airflow has these Preset expressions for readability, such as `None`, `@once`, `@hourly`, `@daily`, `@weekly`, `@monthly`, `@yearly`. By default, if you do not specify a schedule_interval, it is set to daily. 

`end_date`: the date that your dag should stop being scheduled. It is None by default. 

so-called "execution_date" = when the dag actually started to run - schedule_interval

For example, a dag with a start_date of today midnight, with a interval of 1 hr, its first run is 1am today, but this run's declared execution_date is today midnight. 

## Manipulating the start_date with schedule_interval
skipped. 

In the dag's Tree View, can see the run history, their execution time, actual started/ended time, and the scheduled-to-run-at time. The latter two doesn't have to be same. 

## Backfill and Catchup
Sometimes, a task fails, so you need to stop the task scheduling and work on a fix. During this time, the DAG won't be triggered, and will start accumulating delay. 

By default, the catchup param is set to True. e.g., a dag is scheduled to run daily, it ran on day 1, but then got suspended, when it finally got resumed on day 4, the runs that are scheduled to run on day 2 and 3 will also be run. 

This catchup parameter can be set at the dag level or can be set globally using the "catchup_by_default" param in the "airflow.cfg" file. 

The val of this param depends on your use case. There is no best practice. Note that if it is set to True, you may end with many dag runs at the same time, with may cause performance issues. 

## Catching up non triggered DAGRuns
Note that you can still use the "airflow backfill" command in the cli to manually do the backfill, no matter the val of the "catchup" parameter. e.g., `airflow backfill -s 2024-01-20 -e 2024-01-25 --rerun_failed_tasks -B my_dag_name` reruns the failed dags between 20th and 25th. `-B` (backwards) forces the backfill to run tasks starting from the recent days in first. 

Even if the catchup is set to false, when the dag is resumed, the one latest missed dag run will be triggered (Airflow default behavior). 

## Dealing with timezones in Airflow
As a best practice, always use aware datetime objects (aks with timezone specified). Use the "airflow.timezone" functions to create aware datetime objects. Because default datetime object in Python is naive (with no timezone). 

Airflow datetime info is stored in UTC, same as what is shown in the UI. 

## Making your DAGs timezone aware
To handle DST, refer to the commented out code in "03-dags/03-tz_dag.py". Note that with the commented code, the dag will always start at 2am local timezone (this is if catchup is set to true, otherwise the 2am run when DST happens will be skipped). But if you use timedelta here, it will always respect the 24 hrs of time diff. 

## How to make your tasks dependent
Create task dependencies between the current dag run and the prev dag run. 

`depends_on_past`. Default val: False. It is applied a task level. But can also be defined in the default_args dict, to apply to all tasks. Assume for a dag, with tasks a, b, c. At the 1st run, all tasks finished successfully. At the 2nd run, task b failed, so the task c also failed with the status "upstream_failed". Now you want to prevent task b from running in the 3rd dag run, if this task failed in the prv run. 

Set "depends_on_past" to True if you want to run the task only if its last run was successful. 

`wait_for_downstream`. It is applied a task level. But can also be defined in the default_args dict, to apply to all tasks. Enforce the run of a task to wait until its prv run's immediate downstream tasks to finish. This is useful if the different instances of a task X alter the same asset, and this asset is used by tasks downstream of task X. Note that depends_on_past is forced to True wherever wait_for_downstream is used. Also note that only tasks immediately downstream of the previous task instance are waited for; the statuses of any tasks further downstream are ignored.


## Creating task dependencies between DagRuns



## How to structure your DAG folder



## Organizing your DAGs folder



## How the Web Server works



## How to deal with failures in your DAGs



## Retry and Alerting



## How to test your DAGs



## Unit testing your DAGs
































