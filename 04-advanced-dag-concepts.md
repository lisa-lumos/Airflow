# 4. Advanced DAG concepts
## Minimizing Repetitive Patterns With SubDAGs
Use case: many tasks run the same logical function in parallel. e.g.: 3 tasks downloading data from different sources concurrently. 

You can make you DAG cleaner, by grouping these tasks together, using SubDAGs. 

In the DAG graph view, a subDAG is a box with bold borders. 

To create a subDAG, we call the factory method that returns a DAG object, with the tasks we want to combine. Then we can instantiate a SubDagOperator to attach the SubDag to the main Dag. This is how airflow makes the distinction between a dag and a subdag. 

Note that the subdag is still managed by the main dag, so it should have the same start_date and scheduling_interval as its parent, otherwise you may get unexpected behaviors. 

The state of the SubDagOperator and the tasks themselves are independent. e.g., a SubDagOperator marked as success will not affect the underlying tasks that can be still marked as failed. 

The biggest issue with SubDags are deadlocks. Indeed it is possible to specify an executor in SubDags, which is set to the Sequential Executor by default. If you are using Airflow in production with SubDags, and the Celery Executor is set, you may be in trouble. When a SubDagOperator is triggered, it takes a worker slot, and each task in the child dag takes a slot as well, until the entire subdag is finished. Each time a task is triggered, a slot is taken from the default pool, which is limited to 128 by default. If there are no more slots available, it may slow down your task processing, or even get your dag stuck. One way to avoid deadlocks, is by creating a queue, only for SubDags. 

## [Practice] Grouping your tasks with SubDAGs and Deadlocks


## Making different paths in your DAGs with Branching


## [Practice] Make Your First Conditional Task Using Branching


## Trigger rules for your tasks


## [Practice] Changing how your tasks are triggered


## Avoid hard coding values with Variables, Macros and Templates


## [Practice] Templating your tasks


## How to share data between your tasks with XCOMs


## [Practice] Sharing (big?) data with XCOMs


## TriggerDagRunOperator or when your DAG controls another DAG


## [Practice] Trigger a DAG from another DAG


## Dependencies between your DAGs with the ExternalTaskSensor





































