variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "sous-chef"
}

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = "EC2 instance type (free tier: t2.micro or t3.micro)"
  type        = string
  default     = "t2.micro"
}

variable "ssh_key_name" {
  description = "Name of existing AWS SSH key pair"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed to SSH (use your IP, not 0.0.0.0/0)"
  type        = list(string)
  default     = []
}

variable "root_volume_size" {
  description = "Size of root EBS volume in GB"
  type        = number
  default     = 30
}

variable "rds_instance_class" {
  description = "RDS instance class (free tier: db.t2.micro or db.t3.micro)"
  type        = string
  default     = "db.t2.micro"
}

variable "domain_name" {
  description = "Domain name for the application (optional, for SSL setup)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
