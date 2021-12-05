resource "aws_kinesis_stream" "task_stream" {
  name = var.task_stream_name
  shard_count = var.stream_shard_count
  retention_period = var.task_stream_retention_period
  encryption_type = "KMS"
  kms_key_id = concat(data.aws_kms_alias.kms_key.*.id, ["alias/aws/kinesis"])[0]
}