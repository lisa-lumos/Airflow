# 4. Advanced DAG concepts
## Minimizing Repetitive Patterns With SubDAGs
Use case: many tasks run the same logical function in parallel. e.g.: 3 tasks downloading data from different sources concurrently. 

You can make you DAG cleaner, by grouping these tasks together, using SubDAGs. 

In the DAG graph view, a subDAG is a box with bold borders. 

To create a subDAG, we call the factory method that returns a DAG object, with the tasks we want to combine. Then we can instantiate a SubDagOperator to attach the SubDag to the main Dag. This is how airflow makes the distinction between a dag and a subdag. 

Note that the subdag is still managed by the main dag, so it should have the same start_date and scheduling_interval as its parent, otherwise you may get unexpected behaviors. 

The state of the SubDagOperator and the tasks themselves are independent. e.g., a SubDagOperator marked as success will not affect the underlying tasks that can be still marked as failed. 

The biggest issue with SubDags are deadlocks. Indeed it is possible to specify an executor in SubDags, which is set to the Sequential Executor by default. If you are using Airflow in production with SubDags, and the Celery Executor is set, you may be in trouble. When a SubDagOperator is triggered, it takes a worker slot, and each task in the child dag takes a slot as well, until the entire subdag is finished. Each time a task is triggered, a slot is taken from the default pool, which is limited to 128 by default. If there are no more slots available, it may slow down your task processing, or even get your dag stuck. One way to avoid deadlocks, is by creating a queue, only for SubDags. 

The instructor recommend that you stay away from the SubDags, or just stay with the Sequential Executor. 

## Grouping your tasks with SubDAGs and Deadlocks
"subdags/subdag.py":
```py
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator

def factory_subdag(parent_dag_name, child_dag_name, default_args):

    with DAG(
        dag_id='%s.%s' % (parent_dag_name, child_dag_name),
        default_args=default_args
    ) as dag:

        for i in range(5):
            DummyOperator(
                task_id='%s-task-%s' % (child_dag_name, i + 1)
            )

    return dag
```

"test_subdag.py":
```py
import airflow
from subdags.subdag import factory_subdag
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.subdag_operator import SubDagOperator
from airflow.executors.sequential_executor import SequentialExecutor
from airflow.executors.celery_executor import CeleryExecutor

DAG_NAME="test_subdag"

default_args = {
    'owner': 'Airflow',
    'start_date': airflow.utils.dates.days_ago(2)
}

with DAG(dag_id=DAG_NAME, default_args=default_args, schedule_interval="@once") as dag:
    start = DummyOperator(
        task_id='start'
    )

    subdag_1 = SubDagOperator(
        task_id='subdag-1',
        subdag=factory_subdag(DAG_NAME, 'subdag-1', default_args),
        executor=SequentialExecutor() # use CeleryExecutor() for concurrent run
    )

    some_other_task = DummyOperator(
        task_id='check'
    )

    subdag_2 = SubDagOperator(
        task_id='subdag-2',
        subdag=factory_subdag(DAG_NAME, 'subdag-2', default_args),
        executor=SequentialExecutor() # use CeleryExecutor() for concurrent run
    )

    end = DummyOperator(
        task_id='final'
    )

    start >> subdag_1 >> some_other_task >> subdag_2 >> end
```

In the graph view, click on the node of "subdag-1" -> Zoom into Sub DAG -> In the graph view, see the 5 tasks created from the factory method earlier. Open the Grantt view, can see the 5 tasks executed sequentially. Because by default, the SubDagOperator is set with the Sequential Executor, even when Airflow is running with the Celery Executor. 

To make them run concurrently, use the `CeleryExecutor()`. 

When you go to Tree View, you can see that the SubDags are depicted as a task in your parent DAG, and not as a graph of tasks. This is why deadlocks might happen. A subdag is an abstraction of tasks, but still behaves as a task. 

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





































