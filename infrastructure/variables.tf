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

variable "stream_shard_count" {
  type = number # todo create a  specific module to have autoscaling enabled
  default = 1
  description = "Number of shard for the "
}

variable "task_stream_name" {
  type = string
  default = "streamflow_task_stream"
  description = "Name of the aws stream where task will be published"
}

variable "task_stream_retention_period" {
  type = number
  default = 24
  description = "Number of hours for which tasks will be retained (max should be 8760)"
}

variable "encryption_kms_key" {
  type = string
  default = null
  description = "An alias of the kms key to be used to encrypt all data. By default, default aws keys for the service will be used."
}

