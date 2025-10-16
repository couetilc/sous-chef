# Ansible Documentation

## Prerequisites

- Ansible installed (`brew install ansible`)
- SSH key: `~/.ssh/connor-keypair.pem`
- 1Password SSH agent configured at `~/.1password/agent.sock`
- `.env` file in project root

## Folder Structure

```
ansible/
├── inventory.ini    # Host definitions and connection settings
├── setup.yml        # Initial server setup (git, Docker, repo clone)
├── deploy.yml       # Deploy production stack
```

## Helpful Commands

Test connection:
```bash
ansible -i ansible/inventory.ini ec2 -m ping
```

Run ad-hoc commands:
```bash
ansible -i ansible/inventory.ini ec2 -a "command"
```

Initial server setup (run once):
```bash
ansible-playbook -i ansible/inventory.ini ansible/setup.yml
```

Deploy production stack:
```bash
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml
```
