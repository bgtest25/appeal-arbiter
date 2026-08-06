resource "aws_apprunner_service" "app" {
  service_name = "appeal-arbiter"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.app.repository_url}:${var.image_tag}"
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"

        runtime_environment_secrets = {
          ANTHROPIC_API_KEY = aws_secretsmanager_secret.anthropic_api_key.arn
        }
      }
    }

    # Off for now: no image exists in ECR until the first manual push. Flip on
    # once the pipeline pushes new tags routinely.
    auto_deployments_enabled = false
  }

  instance_configuration {
    cpu               = "1024"
    memory            = "2048"
    instance_role_arn = aws_iam_role.apprunner_instance.arn
  }

  health_check_configuration {
    protocol = "HTTP"
    path     = "/health"
  }
}
