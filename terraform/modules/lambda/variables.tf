variable "deployment_file" {
  description = "Path to the Lambda deployment zip file"
  type        = string
  validation {
    condition     = fileexists(var.deployment_file)
    error_message = "Specified Lambda authorizer zip file does not exist."
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
variable "function_timeout" {
  description = "The timeout of the Lambda function execution in seconds"
  type        = number
  default     = 15
}
variable "function_ssm_parameter_names" {
  description = "A set of SSM parameter names to be precreated for the function (env variables will be precreated as well)"
  type        = set(string)
  default     = []
}
