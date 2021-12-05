data "aws_kms_alias" "kms_key" {
  count = var.encryption_kms_key == null ? 0 : 1
  name = var.encryption_kms_key
}
