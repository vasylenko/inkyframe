provider "aws" {
  region  = "us-east-1"
  default_tags {
    tags = local.default_tags
  }
  allowed_account_ids = var.allowed_account_ids
}

