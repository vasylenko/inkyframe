variable "deployment_file" {
  description = "Path to the Lambda deployment zip file"
  type        = string
  validation {
    condition     = fileexists(var.deployment_file)
    error_message = "Specified Lambda authorizer zip file does not exist"
  }
}
variable "project_name" {
  description = "Project name used in default tags"
  type        = string
}
variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}
variable "function_architecture" {
  description = "The architecture of the Lambda function"
  type        = string
  default     = "arm64"
}
variable "function_runtime" {
  description = "The runtime of the Lambda function"
  type        = string
  default     = "provided.al2023"
}
variable "function_timeout" {
  description = "The timeout of the Lambda function execution in seconds"
  type = number
  default = 3
}
variable "function_ssm_parameters" {
  description = "A set of SSM parameter names to be precreated for the function (env variables will be precreated as well)"
  type = set(string)
  default = []
}
variable "function_handler" {
  description = "The function handler (entrypoint)"
  type        = string
  default     = "bootstrap.handler"
}