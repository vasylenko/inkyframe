module "lambda_calendar_backend" {
  source          = "./modules/lambda"
  deployment_file = "../backend-lambda-functions/calendar-backend/deployment.zip"
  function_name   = "calendar-backend"
  project_name    = local.project_name
  function_ssm_parameters = [
    "google-api-oauth-token",
    "google-api-credentials"
  ]
}

module "route_calendars" {
  source                = "./modules/api-gateway-route"
  api_id                = aws_apigatewayv2_api.this.id
  route_key             = "GET /calendars/{calendar-name}"
  api_gw_execution_arn  = aws_apigatewayv2_api.this.execution_arn
  lambda_invocation_arn = module.lambda_calendar_backend.lambda.invoke_arn
  lambda_function_name  = module.lambda_calendar_backend.lambda.function_name
  authorizer_id         = aws_apigatewayv2_authorizer.header_based_authorizer.id
}

#module "lambda_this_day_in_history_backend" {
#  source          = "./modules/lambda"
#  deployment_file = "../backend-lambda-functions/this-day-in-history/deployment.zip"
#  function_name   = "this-day-in-history-backend"
#  project_name    = local.project_name
#}
#
#module "route_this_day_in_history" {
#  source                = "./modules/api-gateway-route"
#  api_id                = aws_apigatewayv2_api.this.id
#  route_key             = "GET /this-day-in-history"
#  api_gw_execution_arn  = aws_apigatewayv2_api.this.execution_arn
#  lambda_invocation_arn = module.lambda_this_day_in_history_backend.lambda.invoke_arn
#  lambda_function_name  = module.lambda_this_day_in_history_backend.lambda.function_name
#  authorizer_id         = aws_apigatewayv2_authorizer.header_based_authorizer.id
#}

#module "lambda_air_monitor_backend" {
#    source          = "./modules/lambda"
#    deployment_file = "../backend-lambda-functions/air-monitor/deployment.zip"
#    function_name   = "air-monitor-backend"
#    project_name    = local.project_name
#}
#
#module "route_air_monitor" {
#    source                = "./modules/api-gateway-route"
#    api_id                = aws_apigatewayv2_api.this.id
#    route_key             = "GET /air-monitor"
#    api_gw_execution_arn  = aws_apigatewayv2_api.this.execution_arn
#    lambda_invocation_arn = module.lambda_air_monitor_backend.lambda.invoke_arn
#    lambda_function_name  = module.lambda_air_monitor_backend.lambda.function_name
#    authorizer_id         = aws_apigatewayv2_authorizer.header_based_authorizer.id
#}