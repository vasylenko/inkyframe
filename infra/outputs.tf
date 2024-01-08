output "lambda_authorizer_environment_variables" {
  value = module.lambda_api_gw_authorizer.lambda.environment[*].variables
}

output "lambda_calendar_backend_variables" {
  value = module.lambda_calendar_backend.lambda.environment[*].variables
}

output "apigateway_routes" {
  value = {
    "Base URL" : aws_apigatewayv2_stage.default.invoke_url,
    "Calendars" : module.route_calendars.route.route_key,
    #    "This day in history": module.lambda_this_day_in_history_backend.route.route_key,
    #    "Air monitor": module.route_air_monitor.route.route_key,
  }
}