output "lambda_authorizer_environment_variables" {
  value = module.lambda_api_gw_authorizer.lambda.environment[*].variables
}

output "lambda_calendar_backend_variables" {
  value = module.lambda_calendar_backend.lambda.environment[*].variables
}