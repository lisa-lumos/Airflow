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



## Catching up non triggered DAGRuns



## Dealing with timezones in Airflow



## Making your DAGs timezone aware



## How to make your tasks dependent



## Creating task dependencies between DagRuns



## How to structure your DAG folder



## Organizing your DAGs folder



## How the Web Server works



## How to deal with failures in your DAGs



## Retry and Alerting



## How to test your DAGs



## Unit testing your DAGs
































