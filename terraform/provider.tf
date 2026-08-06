provider "aws" {
  region  = var.aws_region
  profile = "appeal-arbiter-bootstrap"

  # appeal-arbiter-bootstrap lives in Swypi's management account; assume into
  # the appeal-arbiter member account to actually provision resources there.
  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/OrganizationAccountAccessRole"
    session_name = "terraform-appeal-arbiter"
  }
}
