resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name = "appeal-arbiter/anthropic-api-key"
}

# Deliberately no aws_secretsmanager_secret_version here: the actual key value
# is set out-of-band via the CLI after apply, so it never lands in Terraform
# state or version control. See terraform/README.md for the exact command.
