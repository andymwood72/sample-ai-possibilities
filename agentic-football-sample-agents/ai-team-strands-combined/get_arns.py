#!/usr/bin/env python3
"""
Extract the 5 most recently deployed agent runtime ARNs for ai-team-strands-combined.

Reads from the local deployed-state.json first (instant, no AWS call).
Falls back to a live boto3 call if the state file is missing or stale.

Usage:
    python get_arns.py              # table output
    python get_arns.py --json       # JSON output
    python get_arns.py --live       # force live AWS API call
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
STATE_FILE = SCRIPT_DIR / "agentcore" / ".cli" / "deployed-state.json"

POSITION_ORDER = {
    "ai_gk_combined_agent":   "GK  (player 0)",
    "ai_def_combined_agent":  "DEF (player 1)",
    "ai_mid_combined_agent":  "MID (player 2)",
    "ai_fwd1_combined_agent": "FWD1(player 3)",
    "ai_fwd2_combined_agent": "FWD2(player 4)",
}


def from_state_file():
    """Read ARNs from the local deployed-state.json."""
    if not STATE_FILE.exists():
        return None
    data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    runtimes = (
        data.get("targets", {})
            .get("default", {})
            .get("resources", {})
            .get("runtimes", {})
    )
    if not runtimes:
        return None
    return {
        name: info["runtimeArn"]
        for name, info in runtimes.items()
        if "runtimeArn" in info
    }


def from_aws():
    """Fetch ARNs live from the AWS API."""
    try:
        import boto3
    except ImportError:
        print("ERROR: boto3 not installed. Run: pip install boto3")
        sys.exit(1)

    client = boto3.client("bedrock-agentcore-control")
    paginator = client.get_paginator("list_agent_runtimes")
    arns = {}
    for page in paginator.paginate():
        for rt in page.get("agentRuntimes", []):
            name = rt.get("agentRuntimeName", "")
            arn = rt.get("agentRuntimeArn", "")
            if name in POSITION_ORDER and arn:
                arns[name] = arn
    return arns


def main():
    force_live = "--live" in sys.argv
    as_json = "--json" in sys.argv

    arns = (from_aws() if force_live else from_state_file()) or from_aws()

    if not arns:
        print("No agent ARNs found.")
        sys.exit(1)

    # Sort by position order
    ordered = {
        k: arns[k]
        for k in POSITION_ORDER
        if k in arns
    }

    if as_json:
        print(json.dumps(ordered, indent=2))
        return

    print(f"\n{'Agent':<20} {'Position':<16} ARN")
    print("-" * 110)
    for name, arn in ordered.items():
        pos = POSITION_ORDER.get(name, name)
        short = name.replace("_combined_agent", "")
        print(f"  {short:<18} {pos:<16} {arn}")
    print()


if __name__ == "__main__":
    main()
