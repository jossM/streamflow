resource "aws_dynamodb_table" "tasks" {
  name = var.task_table_name
  hash_key = "id"
  billing_mode = "PAY_PER_REQUEST"
  stream_enabled = false
  attribute {
    name = "id"
    type = "S"  # string
  }
  server_side_encryption {
    enabled = true
  }
  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_dynamodb_table" "tasks_instances" {
  name = var.task_instance_table_name
  hash_key = "id"
  billing_mode = "PAY_PER_REQUEST"
  stream_enabled = false

  attribute {
    name = "id"
    type = "S"  # string
  }

  attribute {
    name = "execution_id"
    type = "S"
  }

  # todo: add time to live attribute ?

  server_side_encryption {
    enabled = true
  }
  point_in_time_recovery {
    enabled = true
  }
}

data "aws_iam_policy_document" "streamflow_admin" {
  version = "2017-10-17"
  statement {
    sid="ListAndDescribe"
    effect="Allow"
    actions= [
      "dynamodb:List*",
      "dynamodb:DescribeReservedCapacity*",
      "dynamodb:DescribeLimits",
      "dynamodb:DescribeTimeToLive"
    ],
    resource = ["*"]
  }
  statement {
    actions = [
      "dynamodb:BatchGet*",
      "dynamodb:DescribeStream",
      "dynamodb:DescribeTable",
      "dynamodb:Get*",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchWrite*",
      "dynamodb:CreateTable",
      "dynamodb:Update*",
      "dynamodb:PutItem"
    ]
    effect = "Allow"
    resources = [
      aws_dynamodb_table.tasks.arn,
      aws_dynamodb_table.tasks_instances.arn
    ]
  }
}

resource "aws_iam_policy" "streamflow_admin" {
  name = var.admin_policy_name
  policy = data.aws_iam_policy_document.streamflow_admin.json
}
