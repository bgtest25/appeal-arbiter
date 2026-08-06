variable "aws_region" {
  description = "AWS region for the appeal-arbiter account"
  type        = string
  default     = "us-east-1"
}

variable "account_id" {
  description = "The appeal-arbiter AWS Organizations member account ID"
  type        = string
  default     = "252922282915"
}

variable "image_tag" {
  description = "ECR image tag for the App Runner service to deploy"
  type        = string
  default     = "latest"
}
