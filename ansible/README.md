# Sous Chef - Ansible Automation

Ansible playbooks for provisioning and deploying the Sous Chef application to AWS EC2 instances.

## Overview

This Ansible configuration automates:
- **Server provisioning**: System updates, Docker installation, security hardening
- **Application deployment**: Git clone, frontend build, Docker Compose deployment
- **Service management**: Systemd service for automatic restarts

## Prerequisites

1. **Ansible** >= 2.14 installed on your local machine
2. **Terraform infrastructure** already deployed (see `../terraform/README.md`)
3. **SSH access** to the EC2 instance
4. **AWS CLI** configured (for local Terraform output access)

### Install Ansible

```bash
# macOS
brew install ansible

# Ubuntu/Debian
sudo apt update
sudo apt install ansible

# Python pip
pip install ansible
```

## Quick Start

### 1. Configure Inventory

After deploying with Terraform, get your instance IP:

```bash
cd ../terraform
terraform output instance_public_ip
```

Update the inventory file with your instance IP:

```bash
cd ../ansible
export TF_OUTPUT_INSTANCE_IP="YOUR_INSTANCE_IP"
export SSH_KEY_NAME="your-key-name"
```

Or manually edit `inventory.yml`:

```yaml
sous-chef-server:
  ansible_host: "YOUR_INSTANCE_IP"
```

### 2. Test Connection

```bash
ansible all -m ping
```

### 3. Provision Server (First Time Only)

```bash
ansible-playbook provision.yml
```

This installs system dependencies, Docker, and performs initial server setup.

### 4. Deploy Application

```bash
ansible-playbook deploy.yml
```

You'll be prompted for:
- **Git repository URL**: Your Sous Chef repository (or leave empty to use existing code)
- **Git branch**: Branch to deploy (default: main)

### 5. Complete Setup (Provision + Deploy)

For a fresh installation:

```bash
ansible-playbook site.yml
```

## Playbooks

### `provision.yml`
Initial server provisioning. Run once after creating infrastructure with Terraform.

**Includes:**
- System updates and security patches
- Common tools (git, curl, vim, etc.)
- Docker and Docker Compose installation
- Swap file configuration
- Security hardening

```bash
ansible-playbook provision.yml
```

### `deploy.yml`
Deploy or update the application. Run whenever you want to deploy new code.

**Includes:**
- Clone/update git repository
- Retrieve secrets from AWS Secrets Manager
- Install Node.js and build frontend static files
- Configure environment variables
- Deploy with Docker Compose
- Start systemd service

```bash
ansible-playbook deploy.yml
```

**Tags:**
```bash
# Deploy only application code
ansible-playbook deploy.yml --tags app

# Run only health checks
ansible-playbook deploy.yml --tags healthcheck
```

### `site.yml`
Complete setup from scratch (provision + deploy).

```bash
ansible-playbook site.yml
```

## Architecture

### Frontend Deployment
The frontend is **built as static files** and served by nginx:

1. Node.js 24.x is installed on the server
2. Frontend dependencies are installed with `pnpm install`
3. Production build runs `pnpm build` (creates `front-end/dist/`)
4. Nginx serves static files from `dist/` directory
5. API requests are proxied to the Django backend

### Backend Deployment
The Django backend runs in Docker:

1. Backend container connects to AWS RDS PostgreSQL
2. Environment variables loaded from `.env` file
3. Secrets retrieved from AWS Secrets Manager
4. Runs via systemd service for auto-restart

### Docker Compose Structure

Production uses two compose files:
- `compose.yml`: Base configuration (from repo)
- `docker-compose.prod.yml`: Production overrides

**Production changes:**
- Local PostgreSQL database disabled (uses AWS RDS)
- Frontend dev server disabled (uses static build)
- Environment variables from `.env` file
- Restart policies enabled
- Read-only volume mounts

## Directory Structure

```
ansible/
├── ansible.cfg              # Ansible configuration
├── inventory.yml            # Host inventory
├── provision.yml            # Server provisioning playbook
├── deploy.yml              # Application deployment playbook
├── site.yml                # Complete setup playbook
├── group_vars/
│   └── all.yml             # Global variables
├── host_vars/              # Host-specific variables
└── roles/
    ├── common/             # Common server setup
    │   ├── tasks/
    │   │   └── main.yml
    ├── docker/             # Docker installation
    │   ├── tasks/
    │   │   └── main.yml
    │   └── handlers/
    │       └── main.yml
    └── application/        # Application deployment
        ├── tasks/
        │   └── main.yml
        ├── templates/
        │   ├── env.j2
        │   ├── docker-compose.prod.yml.j2
        │   ├── nginx.conf.j2
        │   └── sous-chef.service.j2
        └── handlers/
            └── main.yml
```

## Configuration

### Variables

Edit `group_vars/all.yml` to customize:

```yaml
# Project configuration
project_name: sous-chef
environment: production

# Application settings
app_dir: /opt/sous-chef
app_user: ubuntu

# AWS configuration
aws_region: us-east-2

# Database configuration
db_secret_name: "sous-chef/production/db-credentials"
django_secret_name: "sous-chef/production/django-secret-key"

# Django settings
allowed_hosts: "*"  # Set to your domain in production
```

### Host-Specific Variables

Create `host_vars/sous-chef-server.yml` for host-specific overrides:

```yaml
git_repo_url: "https://github.com/yourusername/sous-chef.git"
git_branch: main
domain_name: "sous-chef.example.com"
```

## Managing the Application

### View Application Status

```bash
# SSH into server
ssh -i ~/.ssh/your-key.pem ubuntu@YOUR_INSTANCE_IP

# Check systemd service
sudo systemctl status sous-chef

# View Docker containers
docker ps

# View logs
docker compose -f compose.yml -f docker-compose.prod.yml logs -f
```

### Restart Application

```bash
# Via systemd
sudo systemctl restart sous-chef

# Or directly with Docker Compose
cd /opt/sous-chef
docker compose -f compose.yml -f docker-compose.prod.yml restart
```

### Update Application

```bash
# From your local machine
ansible-playbook deploy.yml
```

### Access Logs

```bash
# Application logs
docker compose -f compose.yml -f docker-compose.prod.yml logs backend
docker compose -f compose.yml -f docker-compose.prod.yml logs nginx

# Follow logs
docker compose -f compose.yml -f docker-compose.prod.yml logs -f
```

## SSL/TLS Configuration (Optional)

To enable HTTPS with Let's Encrypt:

1. Set your domain in `group_vars/all.yml`:
   ```yaml
   domain_name: "sous-chef.example.com"
   ```

2. Point your domain's DNS to the EC2 instance IP

3. Install Certbot and obtain certificate:
   ```bash
   ssh ubuntu@YOUR_INSTANCE_IP
   sudo apt install certbot
   sudo certbot certonly --standalone -d sous-chef.example.com
   ```

4. Uncomment the HTTPS server block in the nginx template (`roles/application/templates/nginx.conf.j2`)

5. Redeploy:
   ```bash
   ansible-playbook deploy.yml
   ```

## Troubleshooting

### Connection Issues

```bash
# Test SSH connection
ssh -i ~/.ssh/your-key.pem ubuntu@YOUR_INSTANCE_IP

# Test Ansible connectivity
ansible all -m ping -vvv
```

### Application Not Starting

```bash
# Check Docker service
ansible production -m shell -a "sudo systemctl status docker" -b

# Check application service
ansible production -m shell -a "sudo systemctl status sous-chef" -b

# View Docker logs
ansible production -m shell -a "cd /opt/sous-chef && docker compose logs" -b
```

### Secrets Not Loading

```bash
# Verify AWS credentials on EC2
ssh ubuntu@YOUR_INSTANCE_IP
aws sts get-caller-identity

# Test secrets retrieval
aws secretsmanager get-secret-value --secret-id sous-chef/production/db-credentials --region us-east-2
```

### Frontend Build Fails

```bash
# Check Node.js version
ansible production -m shell -a "node --version"

# Check pnpm
ansible production -m shell -a "pnpm --version"

# Manually rebuild
ssh ubuntu@YOUR_INSTANCE_IP
cd /opt/sous-chef/front-end
pnpm install
pnpm build
```

## Maintenance Playbooks

### Update System Packages

```bash
ansible-playbook provision.yml --tags common
```

### Rebuild Frontend Only

```bash
ansible production -m shell -a "cd /opt/sous-chef/front-end && pnpm build" -b --become-user ubuntu
```

### Restart Docker

```bash
ansible production -m systemd -a "name=docker state=restarted" -b
```

## Security Best Practices

1. **Restrict SSH Access**: Update security group to allow SSH only from your IP
2. **Use Vault**: Store sensitive variables in Ansible Vault:
   ```bash
   ansible-vault create group_vars/vault.yml
   ansible-playbook deploy.yml --ask-vault-pass
   ```
3. **Update Allowed Hosts**: Set `allowed_hosts` to your actual domain
4. **Enable HTTPS**: Configure SSL/TLS certificates
5. **Regular Updates**: Run `provision.yml` regularly for security patches

## Integration with Terraform

### Automatic Inventory

Set environment variables from Terraform output:

```bash
cd ../terraform
export TF_OUTPUT_INSTANCE_IP=$(terraform output -raw instance_public_ip)
export SSH_KEY_NAME=$(terraform output -raw ssh_key_name)

cd ../ansible
ansible-playbook site.yml
```

### Scripted Deployment

Create a deployment script:

```bash
#!/bin/bash
# deploy.sh

cd terraform
terraform apply -auto-approve
INSTANCE_IP=$(terraform output -raw instance_public_ip)

cd ../ansible
export TF_OUTPUT_INSTANCE_IP=$INSTANCE_IP
ansible-playbook site.yml
```

## Next Steps

After successful deployment:

1. Access your application at `http://YOUR_INSTANCE_IP`
2. Configure Django superuser:
   ```bash
   ssh ubuntu@YOUR_INSTANCE_IP
   cd /opt/sous-chef
   docker compose exec backend python manage.py createsuperuser
   ```
3. Access Django admin at `http://YOUR_INSTANCE_IP/admin`
4. Set up SSL/TLS for production use
5. Configure monitoring and alerting
6. Set up automated backups for RDS

## Additional Resources

- [Ansible Documentation](https://docs.ansible.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
