variable "allowed_account_ids" {
  description = "List of AWS accounts to operate in this Terraform project"
  type        = set(string)
}

locals {
  project_name = "inkyframe"
  repository   = "personal-projects/inkyframe"

  # For provider configuration block in "provider.tf"
  default_tags = {
    project-name = local.project_name
    repository   = local.repository
  }
}

module "lambda_api_gw_authorizer" {
  source          = "./modules/lambda"
  deployment_file = "../backend/lambda-apigw-authorizer/deployment.zip"
  function_name   = "api-gateway-authorizer"
  project_name    = local.project_name
  function_ssm_parameters = [
    "authorization-token"
  ]
}
module "lambda_calendar_backend" {
  source          = "./modules/lambda"
  deployment_file = "../backend/lambda-calendar-backend/deployment.zip"
  function_name   = "calendar-backend"
  project_name    = local.project_name
  function_ssm_parameters = [
    "google-api-oauth-token",
    "google-api-credentials"
  ]
}