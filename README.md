# StreamFlow
###An attempt at event based Airflow on AWS



When dealing with very large dags, airflow scheduler can have trouble dealing with the sheer number of tasks per dag making it slow and hard to manage as it can crash silently.
Another common issue with airflow is the lack of ability to handle event based logic. Usually they are handled with long running dags including sensor triggering the actual execution. Sensors cannot reset so you have to have an idea of the number of events before hands.
This is an attempt to try and solve this issue by revamping the architecture to distribute the work and by applying an event based logic to the executions.

The proposed architecture of the project is the following :
![Architecture schema](https://docs.google.com/drawings/d/e/2PACX-1vQddQMn67sqX9lrnsMMiv5_492TXWmeqEhl_axmJ0bv_haQnsv3zKkJuVjb2p1M-vXt1_-QhKa1_UiC/pub?w=960&amp;h=720)
