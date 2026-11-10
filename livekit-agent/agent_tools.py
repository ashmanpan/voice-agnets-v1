"""Agent tool-use wiring: MCP servers + local skill/function tools.

Lets the LLM call tools mid-conversation so the agent can *do* things on a
call (CRM lookups, scheduling, DB updates, ...), via:
  - MCP servers: external tool providers, configured by the MCP_SERVERS env
    var (comma-separated base URLs). Started/connected by the agent runtime.
  - Local skills: plain async functions registered with @skill and exposed to
    the LLM as function tools.

Plugin imports are lazy so this module (and its config logic) imports and
tests offline, without the livekit agents runtime installed.

Open design questions tracked in the plan before wiring specific tools:
which MCP servers/tasks, what "skill" means, global vs per-call/tenant tools,
and whether money/data-mutating actions run autonomously or need approval.
"""
import os

# Registry of local skills (name -> async callable). Populate with @skill.
_SKILLS: dict = {}


def mcp_server_urls(raw=None):
    """Parse MCP_SERVERS (comma-separated URLs) into a clean list."""
    raw = raw if raw is not None else os.getenv("MCP_SERVERS", "")
    return [u.strip() for u in raw.split(",") if u.strip()]


def mcp_auth_headers():
    """Authorization headers forwarded to MCP servers for IAM-based authz.

    The MCP servers enforce per-identity permissions; the agent presents an
    identity token (MCP_AUTH_TOKEN) rather than deciding authorization itself.
    Empty when no token is configured.
    """
    token = os.getenv("MCP_AUTH_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _default_mcp_factory():
    def make(url, headers=None):
        from livekit.agents import mcp
        if headers:
            return mcp.MCPServerHTTP(url, headers=headers)
        return mcp.MCPServerHTTP(url)
    return make


def build_mcp_servers(urls=None, *, factory=None):
    """Build MCP server objects for the configured URLs (empty => no tools).

    Each server is built with the IAM auth headers so the server can authorize
    the agent's identity.
    """
    urls = urls if urls is not None else mcp_server_urls()
    if not urls:
        return []
    factory = factory or _default_mcp_factory()
    headers = mcp_auth_headers()
    return [factory(u, headers=headers) for u in urls]


def skill(fn):
    """Register a local async function as a callable skill/tool."""
    _SKILLS[fn.__name__] = fn
    return fn


def registered_skills():
    """Return the registered local skills (name -> callable)."""
    return dict(_SKILLS)
