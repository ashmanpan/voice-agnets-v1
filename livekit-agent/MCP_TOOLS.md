# Agent Tool Use (MCP) — configuration

The voice agent can call tools mid-conversation (function-calling) so it can
*do* things during a call, not just talk.

## Model (per decisions)
- **Tools come from external MCP servers** (not local functions). The agent
  discovers each server's tools and exposes them to the LLM.
- **Global scope**: the same tool set is configured on the worker and used for
  every call.
- **IAM-based authorization**: the agent presents an identity token to the MCP
  servers; the **servers** enforce per-identity permissions. The agent does not
  decide authorization itself and does not gate mutations on caller
  confirmation.

## Configure
Set these in the agent's environment (`livekit-agent/.env`):

```
MCP_SERVERS=https://tools.internal/scheduling,https://tools.internal/tickets
MCP_AUTH_TOKEN=<IAM identity token / OIDC bearer>
```

- `MCP_SERVERS` — comma-separated MCP server base URLs. Empty = no tools
  (the agent runs exactly as before).
- `MCP_AUTH_TOKEN` — forwarded as `Authorization: Bearer <token>` to every
  MCP server for IAM-based authz.

Requires the `mcp` package (in `requirements.txt`). Works in both `cascade`
and `realtime` pipeline modes.

## Intended tool categories (what the MCP servers should expose)
- **Scheduling / calendar** — book, reschedule, check callbacks.
- **This app's data** — update task status, notes, action items.
- **Ticketing / knowledge base** — create tickets, look up FAQs.
- **Task management** — assign/fetch tasks for the contact.

## Still to provide
The concrete MCP server URLs for each category above, and the IAM token
issuance mechanism, are deployment-specific — plug them into the env vars
above. Code wiring is complete and tested (URL parsing, auth-header
forwarding, build + session attachment).
