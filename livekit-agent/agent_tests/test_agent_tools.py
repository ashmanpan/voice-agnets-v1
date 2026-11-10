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
        ["http://a", "http://b"], factory=lambda u: ("S", u)
    )
    assert servers == [("S", "http://a"), ("S", "http://b")]


def test_build_mcp_servers_empty_when_none_configured():
    assert agent_tools.build_mcp_servers([]) == []
