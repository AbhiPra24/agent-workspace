---
name: mcp-builder
description: >-
  Guides the design, implementation, testing, and distribution of Model Context Protocol (MCP)
  servers in Python or TypeScript according to the official MCP specifications.
  Trigger with `/new-mcp-server [server_name]`.
parameters:
  name:
    type: string
    description: Name of the MCP server to create
    required: true
  language:
    type: string
    description: Implementation language (python | typescript)
    default: python
---

# MCP Server Builder Skill

End-to-end guidance for developing production-grade Model Context Protocol (MCP) servers.

## Core Capabilities
- **Architecture**: Define Tools, Resources, and Prompts using standard MCP schemas.
- **Transport Support**: Configure stdio (standard input/output) or SSE (Server-Sent Events) transports.
- **Validation**: Test tool schemas with Pydantic (Python) or Zod (TypeScript).
- **Integration**: Generate ready-to-use configuration JSON for Claude Desktop, Cursor, and Antigravity.

## Standard Project Layout

### Python (FastMCP / MCP SDK)
```text
mcp-server-example/
├── server.py              # Main FastMCP server definitions
├── requirements.txt       # Dependencies (mcp>=1.0.0, etc.)
└── README.md              # Installation & configuration guide
```

### TypeScript (MCP TypeScript SDK)
```text
mcp-server-example/
├── src/
│   └── index.ts           # Server entrypoint with Server instance
├── package.json           # @modelcontextprotocol/sdk dependency
└── tsconfig.json
```

## Best Practices
1. **Clear Tool Descriptions**: Write descriptive docstrings explaining tool intent, input schemas, and expected output.
2. **Error Handling**: Return structured error responses instead of crashing the stdio process.
3. **Environment Security**: Never hardcode API keys; load them from environment variables.
