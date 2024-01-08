locals {
  project_name = "inkyframe"
  repository   = "personal-projects/inkyframe"

  # For provider configuration block in "provider.tf"
  default_tags = {
    project-name = local.project_name
    repository   = local.repository
  }
}
