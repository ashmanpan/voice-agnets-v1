"""Offline tests for MCP server config parsing and construction. The real
MCP connection is integration; here we pin the pure config logic with an
injected factory so no network/plugin is needed."""
import agent_tools


def test_mcp_urls_parses_comma_separated():
    assert agent_tools.mcp_server_urls("http://a, http://b ,") == ["http://a", "http://b"]


def test_mcp_urls_empty_is_empty():
    assert agent_tools.mcp_server_urls("") == []


def test_build_mcp_servers_uses_factory():
    servers = agent_tools.build_mcp_servers(
        ["http://a", "http://b"], factory=lambda u, headers=None: ("S", u)
    )
    assert servers == [("S", "http://a"), ("S", "http://b")]


def test_build_mcp_servers_empty_when_none_configured():
    assert agent_tools.build_mcp_servers([]) == []


def test_mcp_auth_headers_empty_without_token(monkeypatch):
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
    assert agent_tools.mcp_auth_headers() == {}


def test_mcp_auth_headers_bearer_with_token(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "tok123")
    assert agent_tools.mcp_auth_headers() == {"Authorization": "Bearer tok123"}


def test_build_mcp_servers_forwards_auth_headers(monkeypatch):
    """IAM-based authz: the agent forwards an identity token so the MCP server
    can authorize per-identity."""
    monkeypatch.setenv("MCP_AUTH_TOKEN", "tok123")
    captured = {}

    def factory(url, headers=None):
        captured[url] = headers
        return (url, headers)

    servers = agent_tools.build_mcp_servers(["http://a"], factory=factory)
    assert servers == [("http://a", {"Authorization": "Bearer tok123"})]
