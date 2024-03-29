variable "allowed_account_ids" {
  description = "List of AWS accounts to operate in this Terraform project"
  type        = set(string)
}
