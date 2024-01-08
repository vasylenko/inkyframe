resource "aws_api_gateway_account" "this" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch_logs.arn
}

resource "aws_iam_role" "api_gateway_cloudwatch_logs" {
  name = "api-gateway-cloudwatch-logs"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"]
}

resource "aws_cloudwatch_log_group" "api_gateway_logs_inkyframe" {
  name              = "/aws/apigateway/inkyframe"
  log_group_class   = "STANDARD"
  retention_in_days = 7
}

resource "aws_apigatewayv2_api" "this" {
  name          = local.project_name
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_authorizer" "header_based_authorizer" {
  api_id                            = aws_apigatewayv2_api.this.id
  authorizer_type                   = "REQUEST"
  name                              = "header-based-authorizer"
  authorizer_payload_format_version = "2.0"
  authorizer_uri                    = module.lambda_api_gw_authorizer.lambda.invoke_arn
  enable_simple_responses           = true
  identity_sources                  = ["$request.header.authorization"]
  authorizer_result_ttl_in_seconds  = 3600
}

resource "aws_lambda_permission" "allow_api_gw_invoke_authorizer" {
  statement_id  = "allowInvokeFromAPIGatewayAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_api_gw_authorizer.lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/authorizers/${aws_apigatewayv2_authorizer.header_based_authorizer.id}"
}


module "route_calendars" {
  source               = "./modules/api-gateway-route"
  api_id               = aws_apigatewayv2_api.this.id
  route_key            = "GET /calendars/{calendar-name}"
  api_gw_execution_arn = aws_apigatewayv2_api.this.execution_arn
  integration_uri      = module.lambda_calendar_backend.lambda.invoke_arn
  lambda_function_name = module.lambda_calendar_backend.lambda.function_name
  authorizer_id        = aws_apigatewayv2_authorizer.header_based_authorizer.id
}


resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true
  description = "Default stage (i.e., Production mode)"
  default_route_settings {
    throttling_burst_limit = 1
    throttling_rate_limit  = 1
  }
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs_inkyframe.arn
    format = jsonencode({
      requestId                 = "$context.requestId",
      authorizerError           = "$context.authorizer.error",
      authorizerPrincipalId     = "$context.authorizer.principalId",
      requestErrorMessage       = "$context.error.message",
      requestErrorMessageString = "$context.error.messageString",
      identityAccountId         = "$context.identity.accountId",
      identityCaller            = "$context.identity.caller",
      identitySourceIP          = "$context.identity.sourceIp",
      identityUser              = "$context.identity.user",
      identityUserArn           = "$context.identity.userArn",
      integrationError          = "$context.integration.error",
      integrationStatus         = "$context.integration.integrationStatus",
      integrationStatusCode     = "$context.integration.status",
      integrationRequestId      = "$context.integration.requestId",
      integrationLatency        = "$context.integration.latency",
      integrationErrorMessage   = "$context.integration.errorMessage"
    })
    #   see for details https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-logging-variables.html
  }
}
