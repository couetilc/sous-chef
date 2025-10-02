# AWS Secrets Manager for Database Credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.project_name}/${var.environment}/db-credentials"
  description = "PostgreSQL database credentials"

  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id

  secret_string = jsonencode({
    username = aws_db_instance.postgres.username
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.postgres.address
    port     = aws_db_instance.postgres.port
    dbname   = aws_db_instance.postgres.db_name
  })
}

# AWS Secrets Manager for Django Secret Key
resource "aws_secretsmanager_secret" "django_secret" {
  name        = "${var.project_name}/${var.environment}/django-secret-key"
  description = "Django SECRET_KEY for cryptographic signing"

  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-django-secret"
  }
}

resource "aws_secretsmanager_secret_version" "django_secret" {
  secret_id = aws_secretsmanager_secret.django_secret.id

  secret_string = jsonencode({
    secret_key = random_password.django_secret.result
  })
}
