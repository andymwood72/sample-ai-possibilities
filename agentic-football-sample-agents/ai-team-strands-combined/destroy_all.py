#!/usr/bin/env python3
"""
Destroy all AI Team (Combined) agents and supporting infrastructure.

Usage:
    python destroy_all.py

Tears down the CloudFormation stack created by deploy_all.py, which removes:
  - All 5 agent runtimes
  - The tactical-tools MCP Gateway and its 4 Lambda functions
  - The team_memory AgentCore Memory resource
  - All associated IAM roles and policies
"""

import json
import os
import sys
import shutil
import subprocess
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent.resolve()


def resolve_exe(name):
    path = shutil.which(name)
    if path is None:
        print(f"ERROR: '{name}' not found on PATH.")
        sys.exit(1)
    return path


def run(cmd, **kwargs):
    cmd = [resolve_exe(cmd[0]), *cmd[1:]]
    print(f"  > {' '.join(str(c) for c in cmd)}")
    kwargs.setdefault("env", os.environ.copy())
    kwargs["env"].setdefault("PYTHONIOENCODING", "utf-8")
    subprocess.run(cmd, check=True, **kwargs)


def aws_cli(*args):
    result = subprocess.run(
        [resolve_exe("aws"), *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    return result.stdout.strip() if result.returncode == 0 else None


print("==========================================")
print("  AI Team (Combined) — Destroy Agents")
print("==========================================\n")

account_id = aws_cli("sts", "get-caller-identity", "--query", "Account", "--output", "text")
if not account_id:
    print("ERROR: Could not resolve AWS account. Check your credentials.")
    sys.exit(1)
region = (
    os.environ.get("AWS_REGION")
    or os.environ.get("AWS_DEFAULT_REGION")
    or aws_cli("configure", "get", "region")
    or "us-east-1"
)
print(f"  AWS Account: {account_id}")
print(f"  AWS Region:  {region}")
print()

try:
    run(
        ["agentcore", "destroy", "--yes"],
        cwd=SCRIPT_DIR,
        env={**os.environ, "AWS_DEFAULT_REGION": region},
    )
except subprocess.CalledProcessError:
    print("\nDestroy failed. Check the output above.")
    sys.exit(1)

print()
print("All combined agents and infrastructure destroyed.")
