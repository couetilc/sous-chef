# EC2 Instance Outputs
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance (Elastic IP)"
  value       = aws_eip.app.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_eip.app.public_dns
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "RDS instance address"
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.postgres.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.postgres.db_name
}

# Secrets Manager Outputs
output "db_credentials_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "django_secret_arn" {
  description = "ARN of the Django secret key secret"
  value       = aws_secretsmanager_secret.django_secret.arn
}

# SSH Connection Command
output "ssh_connection_command" {
  description = "Command to SSH into the instance"
  value       = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ubuntu@${aws_eip.app.public_ip}"
}

# Ansible Inventory Information
output "ansible_inventory_info" {
  description = "Information for Ansible inventory"
  value = {
    host            = aws_eip.app.public_ip
    user            = "ubuntu"
    ssh_key         = var.ssh_key_name
    rds_endpoint    = aws_db_instance.postgres.endpoint
    secrets_db      = aws_secretsmanager_secret.db_credentials.name
    secrets_django  = aws_secretsmanager_secret.django_secret.name
  }
}
