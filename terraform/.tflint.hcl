config {
  plugin_dir = ".tflint.d/plugins"

  call_module_type = "local"
  force = false
  disabled_by_default = false
}
plugin "aws" {
  enabled = true
  version = "0.30.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}
plugin "terraform" {
  enabled = true
}