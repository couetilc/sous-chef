# Sous Chef - Terraform Infrastructure

This Terraform configuration deploys the Sous Chef Django application infrastructure on AWS, optimized for the AWS Free Tier.

## Infrastructure Overview

- **EC2 Instance**: Ubuntu 24.04 LTS (t2.micro) with Elastic IP
- **RDS Database**: PostgreSQL 16.3 (db.t2.micro, 20GB storage)
- **Security**: VPC security groups, IAM roles, encrypted storage
- **Secrets**: AWS Secrets Manager for database credentials and Django secret key

## Prerequisites

1. **AWS Account** with Free Tier eligibility
2. **Terraform** >= 1.5 installed
3. **AWS CLI** configured with appropriate credentials
4. **SSH Key Pair** created in AWS EC2 console

## Setup Instructions

### 1. Create SSH Key Pair (if needed)

```bash
# In AWS Console: EC2 → Key Pairs → Create Key Pair
# Or via AWS CLI:
aws ec2 create-key-pair --key-name sous-chef-key --query 'KeyMaterial' --output text > ~/.ssh/sous-chef-key.pem
chmod 400 ~/.ssh/sous-chef-key.pem
```

### 2. Configure Variables

Copy the example variables file:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and update:

```hcl
# Required: Your SSH key name
ssh_key_name = "sous-chef-key"

# Required: Your IP address for SSH access
# Get your IP: curl -s https://checkip.amazonaws.com
allowed_ssh_cidr = ["YOUR.IP.ADDRESS.HERE/32"]
```

### 3. Initialize and Deploy

```bash
# Initialize Terraform
terraform init

# Review the planned changes
terraform plan

# Apply the configuration
terraform apply
```

Type `yes` when prompted to confirm.

## Outputs

After deployment, Terraform outputs:

- **instance_public_ip**: Public IP address of your EC2 instance
- **ssh_connection_command**: Ready-to-use SSH command
- **rds_endpoint**: Database endpoint for application configuration
- **db_credentials_secret_arn**: ARN for database credentials in Secrets Manager
- **django_secret_arn**: ARN for Django secret key in Secrets Manager

View outputs anytime:

```bash
terraform output
```

## Connecting to Your Instance

```bash
# SSH into the instance
ssh -i ~/.ssh/sous-chef-key.pem ubuntu@<instance_public_ip>

# Or use the output command
terraform output -raw ssh_connection_command | bash
```

## Retrieving Secrets

Database credentials and Django secret key are stored in AWS Secrets Manager:

```bash
# Get database credentials
aws secretsmanager get-secret-value --secret-id sous-chef/production/db-credentials --query SecretString --output text | jq

# Get Django secret key
aws secretsmanager get-secret-value --secret-id sous-chef/production/django-secret-key --query SecretString --output text | jq
```

The EC2 instance has IAM permissions to retrieve these secrets automatically.

## Cost Considerations

This configuration is optimized for AWS Free Tier:

- **EC2**: 750 hours/month of t2.micro (first 12 months)
- **RDS**: 750 hours/month of db.t2.micro + 20GB storage (first 12 months)
- **EBS**: 30GB encrypted storage (first 12 months)
- **Elastic IP**: Free while attached to running instance

**Note**: Costs may apply after Free Tier limits are exceeded or after 12 months.

## Security Features

- **Encrypted Storage**: Both EC2 root volume and RDS storage are encrypted
- **IMDSv2**: EC2 instance requires IMDSv2 for metadata access
- **Restricted SSH**: SSH access limited to specified IP addresses
- **Database Isolation**: RDS only accessible from application server
- **Secrets Management**: Credentials stored in AWS Secrets Manager, not hardcoded
- **Automated Backups**: RDS backups retained for 7 days

## Remote State (Optional)

To enable remote state storage in S3 (recommended for teams):

1. Create an S3 bucket:
```bash
aws s3api create-bucket --bucket sous-chef-terraform-state --region us-east-2 --create-bucket-configuration LocationConstraint=us-east-2
aws s3api put-bucket-versioning --bucket sous-chef-terraform-state --versioning-configuration Status=Enabled
```

2. Uncomment the backend configuration in `main.tf`:
```hcl
backend "s3" {
  bucket = "sous-chef-terraform-state"
  key    = "production/terraform.tfstate"
  region = "us-east-2"
  encrypt = true
}
```

3. Re-initialize Terraform:
```bash
terraform init -migrate-state
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete your EC2 instance, RDS database, and all associated data. A final snapshot will be created for the database.

## Next Steps

After infrastructure deployment:

1. SSH into the EC2 instance
2. Install Docker or configure your Django application
3. Configure your application to use the RDS endpoint and Secrets Manager
4. Set up SSL/TLS certificates (e.g., with Let's Encrypt)
5. Configure a reverse proxy (e.g., Nginx)

## Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `aws_region` | AWS region for deployment | `us-east-2` | No |
| `project_name` | Project name for resource naming | `sous-chef` | No |
| `environment` | Environment name | `production` | No |
| `instance_type` | EC2 instance type | `t2.micro` | No |
| `ssh_key_name` | AWS SSH key pair name | - | **Yes** |
| `allowed_ssh_cidr` | CIDR blocks for SSH access | `[]` | **Yes** |
| `root_volume_size` | Root EBS volume size (GB) | `30` | No |
| `rds_instance_class` | RDS instance class | `db.t2.micro` | No |
| `domain_name` | Domain name for SSL setup | `""` | No |

## Troubleshooting

### SSH Connection Issues
- Verify your IP is in `allowed_ssh_cidr`
- Check security group rules: `aws ec2 describe-security-groups`
- Ensure SSH key permissions: `chmod 400 ~/.ssh/your-key.pem`

### Database Connection Issues
- Verify RDS security group allows traffic from EC2
- Check RDS endpoint: `terraform output rds_endpoint`
- Retrieve credentials from Secrets Manager

### Terraform State Issues
- If state is corrupted, use `terraform refresh`
- For state conflicts with remote backend, use `terraform force-unlock`
