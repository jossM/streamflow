output "tasks_table_arn" {
  value = aws_dynamodb_table.tasks.arn
}

output "task_instances_table_arn" {
  value = aws_dynamodb_table.tasks_instances.arn
}

output "dynamodb_admin_iam_policy_arn" {
  value = aws_iam_policy.streamflow_admin.arn
}
