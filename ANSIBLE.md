# Ansible Documentation

## Prerequisites

- Ansible installed (`brew install ansible`)
- SSH key: `~/.ssh/connor-keypair.pem`
- 1Password SSH agent configured at `~/.1password/agent.sock`

## Folder Structure

```
ansible/
├── inventory.ini    # Host definitions and connection settings
├── setup.yml        # Initial setup playbook (git install & repo clone)
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

Run setup playbook:
```bash
ansible-playbook -i ansible/inventory.ini ansible/setup.yml
```
