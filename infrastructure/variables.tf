############
# task table

variable "task_table_name" {
  type = string
  description = "AWS Dynamodb table name listing task that can be executed"
  default = "streamflow_tasks"
}

#####################
# task_instance table

variable "task_instance_table_name" {
  type = string
  description = "AWS Dynamodb table name listing task execution information"
  default = "streamflow_task_instances"
}

##################################
# admin policy to interact with db
variable "admin_policy_name" {
  type = string
  description = "Name of the iam policy that allows admin access to database tables"
  default = "StreamflowDbAdmin"
}
