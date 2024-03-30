data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}
data "aws_kms_alias" "lambda" {
  name = "alias/aws/lambda"
}
data "aws_caller_identity" "this" {}
data "aws_region" "this" {}