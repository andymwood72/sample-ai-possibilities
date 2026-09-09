"""Combined agent factory: AgentCore Gateway (MCP tools) + AgentCore Memory (STM).

Staged into each agent directory by deploy_all.py as combined_agent_base.py.
Each agent imports create_combined_agent() and create_combined_agent_cdk()
for the legacy-shell and CDK deploy flows respectively.
"""

import os
import httpx2
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamable_http_client
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig


# ---------------------------------------------------------------------------
# Transport factory (shared by both flows)
# ---------------------------------------------------------------------------

def _make_transport(gateway_url: str) -> object:
    """Return a streamable_http_client context manager for the given URL.

    Auth is NONE for the tactical-tools gateway, so no headers are required.
    An httpx2.AsyncClient is only created when a bearer token is present
    (GATEWAY_ACCESS_TOKEN env var) so the default MCP timeouts apply when
    no token is set.
    """
    headers = {}
    access_token = os.environ.get("GATEWAY_ACCESS_TOKEN")
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    http_client = httpx2.AsyncClient(headers=headers) if headers else None
    return streamable_http_client(gateway_url, http_client=http_client)


# ---------------------------------------------------------------------------
# Legacy shell-flow factory (GATEWAY_URL + MEMORY_ID env vars)
# ---------------------------------------------------------------------------

def create_combined_agent(
    system_prompt: str,
    player_id: int,
    position_label: str,
    model_id: str = "us.amazon.nova-micro-v1:0",
) -> tuple[Agent, MCPClient]:
    """Create a Strands Agent with Gateway MCP tools AND AgentCore Memory.

    Required env vars (legacy shell flow):
      GATEWAY_URL  — AgentCore Gateway MCP endpoint
      MEMORY_ID    — AgentCore Memory resource ID
      TEAM_ID      — used as actor_id / session_id prefix (optional)

    Returns:
      (agent, mcp_client) — use `with mcp_client:` when invoking.
    """
    gateway_url = os.environ.get("GATEWAY_URL")
    if not gateway_url:
        raise RuntimeError("GATEWAY_URL environment variable is required")

    memory_id = os.environ.get("MEMORY_ID")
    if not memory_id:
        raise RuntimeError("MEMORY_ID environment variable is required")

    team_id = os.environ.get("TEAM_ID", "default-team")

    return _build_agent(
        system_prompt=system_prompt,
        player_id=player_id,
        position_label=position_label,
        model_id=model_id,
        gateway_url=gateway_url,
        memory_id=memory_id,
        team_id=team_id,
    )


# ---------------------------------------------------------------------------
# CDK flow factory (env vars injected by the CDK stack)
# ---------------------------------------------------------------------------

def create_combined_agent_cdk(
    system_prompt: str,
    player_id: int,
    position_label: str,
    model_id: str = "us.amazon.nova-micro-v1:0",
) -> tuple[Agent, MCPClient]:
    """Create a Strands Agent with Gateway MCP tools AND AgentCore Memory.

    Required env vars (CDK flow — injected automatically by the stack):
      AGENTCORE_GATEWAY_TACTICAL_TOOLS_URL — gateway MCP endpoint
      MEMORY_TEAM_MEMORY_ID                — AgentCore Memory resource ID
      TEAM_ID                              — optional session prefix

    Returns:
      (agent, mcp_client) — use `with mcp_client:` when invoking.
    """
    gateway_url = os.environ.get("AGENTCORE_GATEWAY_TACTICAL_TOOLS_URL")
    if not gateway_url:
        raise RuntimeError(
            "AGENTCORE_GATEWAY_TACTICAL_TOOLS_URL is required. "
            "It is injected automatically by `python deploy_all.py`."
        )

    memory_id = os.environ.get("MEMORY_TEAM_MEMORY_ID")
    if not memory_id:
        raise RuntimeError(
            "MEMORY_TEAM_MEMORY_ID is required. "
            "It is injected automatically by `python deploy_all.py`."
        )

    team_id = os.environ.get("TEAM_ID", "default-team")

    return _build_agent(
        system_prompt=system_prompt,
        player_id=player_id,
        position_label=position_label,
        model_id=model_id,
        gateway_url=gateway_url,
        memory_id=memory_id,
        team_id=team_id,
    )


# ---------------------------------------------------------------------------
# Shared builder
# ---------------------------------------------------------------------------

def _build_agent(
    system_prompt: str,
    player_id: int,
    position_label: str,
    model_id: str,
    gateway_url: str,
    memory_id: str,
    team_id: str,
) -> tuple[Agent, MCPClient]:
    """Wire up memory session manager, MCP client, and Strands agent."""

    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=AgentCoreMemoryConfig(
            memory_id=memory_id,
            session_id=f"match-{team_id}-{position_label}",
            actor_id=f"{team_id}-{position_label}",
        ),
        region_name=os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"),
    )

    def _transport_factory():
        return _make_transport(gateway_url)

    mcp_client = MCPClient(_transport_factory)
    model = BedrockModel(model_id=model_id)

    # Fetch tool definitions while the MCP connection is live
    with mcp_client:
        tools = mcp_client.list_tools_sync()

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools,
        session_manager=session_manager,
    )

    return agent, mcp_client
