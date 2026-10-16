#!/bin/bash
set -e

# Configure git credential helper via gh CLI (reads GITHUB_TOKEN / GH_TOKEN from env)
# This enables both `gh issue create/close` and `git push` over HTTPS
gh auth setup-git 2>/dev/null || true

exec n8n start
