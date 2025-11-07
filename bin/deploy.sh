#!/usr/bin/env -S uv run --with ansible -- bash
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml
