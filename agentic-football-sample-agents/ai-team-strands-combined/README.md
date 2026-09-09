# AI Team — Combined (Gateway + Memory)

The most capable variant of the AI football team. Each agent has:

- **AgentCore Gateway MCP tools** — real-time tactical analysis via 4 Lambda tools
- **AgentCore Memory (STM)** — cross-tick recall so agents remember what happened earlier in the match
- **Match feedback** — all three defeat lessons applied (DEF MARK-first priority, FWD passing when not in shooting range, GK/MID transition awareness after goals)

## Capability comparison

| Variant | LLM | MCP Tools | Memory |
|---|---|---|---|
| `ai-team-strands-balanced` | ✅ | ❌ | ❌ |
| `ai-team-strands-gateway` | ✅ | ✅ | ❌ |
| `ai-team-strands-memory` | ✅ | ❌ | ✅ |
| **`ai-team-strands-combined`** | ✅ | ✅ | ✅ |

## MCP Tools (via tactical-tools Gateway)

| Tool | Used by |
|---|---|
| `calculate_pass_options` | GK, DEF, MID, FWD1, FWD2 |
| `evaluate_shot` | MID, FWD1, FWD2 |
| `find_open_space` | DEF, MID, FWD1, FWD2 |
| `get_defensive_assignment` | GK, DEF, MID |

## Memory (AgentCore STM — `team_memory`)

Each position gets its own session (`match-{team_id}-{position_label}`) with 7-day event expiry. Agents use recalled history to:
- Adapt shot placement based on goalkeeper tendencies
- Avoid passing lanes that were intercepted earlier
- Recognise and exploit recurring opponent patterns
- Tighten marking on forwards who made dangerous runs before

## Deploy

```bash
python deploy_all.py
```

Requires: `agentcore >= 0.25.0`, `aws-cdk`, `uv`, AWS credentials.

The CDK stack creates everything in one pass:
- 5 agent runtimes
- 4 Lambda tool functions + tactical-tools MCP Gateway
- team_memory AgentCore Memory resource
- All IAM roles and environment variable injection

## Destroy

```bash
python destroy_all.py
```
