data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}
data "aws_caller_identity" "this" {}
data "aws_region" "this" {}