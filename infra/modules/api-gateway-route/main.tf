resource "aws_apigatewayv2_route" "this" {
  api_id             = var.api_id
  route_key          = var.route_key
  authorization_type = "CUSTOM"
  authorizer_id      = var.authorizer_id
  target             = "integrations/${aws_apigatewayv2_integration.this.id}"
}

resource "aws_apigatewayv2_integration" "this" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  connection_type        = "INTERNET"
  integration_uri        = var.lambda_invocation_arn
  payload_format_version = "2.0"
}

resource "aws_lambda_permission" "this" {
  statement_id  = "allowInvokeFromAPIGatewayRoute"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gw_execution_arn}/*/*/*/*"
}
