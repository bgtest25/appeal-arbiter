resource "aws_ecr_repository" "app" {
  name                 = "appeal-arbiter"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
