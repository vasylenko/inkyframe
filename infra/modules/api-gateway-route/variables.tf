variable "api_id" {
  description = "The HTTP API identifier."
  type        = string
}
variable "route_key" {
  description = "The route key for the route, e.g, GET /foo/bar."
  type        = string
}
variable "authorizer_id" {
  description = "The identifier of the Authorizer to use on this route."
  type        = string
  default     = null
}
variable "integration_uri" {
  description = "The Invocation ARN of the Lambda function."
  type        = string
}
variable "lambda_function_name" {
  description = "The name of the Lambda function to integrate with the route."
  type        = string
}
variable "api_gw_execution_arn" {
  description = "The Execution ARN of the API Gateway V2 HTTP API that invokes a Lambda function."
  type        = string
}