locals {
  full_function_name = "${var.project_name}-${var.function_name}"
}
resource "aws_lambda_function" "this" {
  function_name = local.full_function_name
  role          = aws_iam_role.this.arn
  architectures = ["arm64"]
  filename      = var.deployment_file
  package_type  = "Zip"
  runtime       = "provided.al2023"
  handler       = "bootstrap.handler"
  timeout       = var.function_timeout
  environment {
    variables = { for item in var.function_ssm_parameter_names : upper(replace(item, "-", "_")) => aws_ssm_parameter.function_ssm_parameters[item].name }
  }
}

resource "aws_ssm_parameter" "function_ssm_parameters" {
  for_each = var.function_ssm_parameter_names
  name     = "/projects/${var.project_name}/lambda/${var.function_name}/${each.value}"
  type     = "SecureString"
  key_id   = data.aws_kms_alias.ssm.arn
  value    = "1"
  lifecycle {
    ignore_changes = [
      value,
    ]
  }
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${local.full_function_name}"
  log_group_class   = "STANDARD"
  retention_in_days = 7
}

resource "aws_iam_role" "this" {
  name                  = local.full_function_name
  force_detach_policies = true
  max_session_duration  = 3600
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "this" {
  name   = "function-permissions"
  role   = aws_iam_role.this.name
  policy = data.aws_iam_policy_document.this.json
}

data "aws_iam_policy_document" "this" {
  statement {
    sid = "writeLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    effect = "Allow"
    resources = [
      "${aws_cloudwatch_log_group.this.arn}:*"
    ]
  }
  statement {
    sid       = "createLogGroup"
    actions   = ["logs:CreateLogGroup"]
    effect    = "Allow"
    resources = ["arn:aws:logs:${data.aws_region.this.id}:${data.aws_caller_identity.this.id}:*"]
  }
  statement {
    sid = "workWithSSMParameters"
    actions = [
      "ssm:GetParameter",
      "ssm:PutParameter"
    ]
    effect    = "Allow"
    resources = [for item in aws_ssm_parameter.function_ssm_parameters : item.arn]
  }
}
