# Ghidra MCP Bridge

This project provides a Python-based bridge to connect **Claude Desktop** and **Gemini CLI** to **Ghidra** using the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). 

It acts as an intermediary that:
1.  **Listens** to Claude Desktop or Gemini CLI via Standard Input/Output (Stdio).
2.  **Proxies** requests to Ghidra's [GhidrAssistMCP](https://github.com/jtang613/GhidrAssistMCP) server via Server-Sent Events (SSE) and HTTP.

This is necessary because Claude Desktop and Gemini CLI primarily consume local MCP servers via Stdio, while the Ghidra plugin exposes an SSE endpoint.

## Prerequisites

*   **Python 3.10+** installed on your system.
*   **Claude Desktop** app installed (or **Gemini CLI** configured).
*   **Ghidra** installed.
*   [**GhidrAssistMCP**](https://github.com/jtang613/GhidrAssistMCP) plugin installed in Ghidra.

## Installation

1.  Clone or download this repository.
2.  Install the required Python dependencies:

    ```bash
    pip3 install -r requirements.txt
    ```

## Usage

### 1. Start Ghidra
Ensure Ghidra is running and the **GhidrAssistMCP** server is active. By default, it listens on `http://127.0.0.1:8080/sse`.

### 2. Configure Claude Desktop
You need to tell Claude Desktop how to launch this bridge. Open your configuration file:

*   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
*   **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add the following entry to the `mcpServers` object:

```json
{
  "mcpServers": {
    "ghidra": {
      "command": "python3",
      "args": [
        "/absolute/path/to/ghidra_mcp_bridge/ghidra_mcp_sse_bridge.py"
      ]
    }
  }
}
```

> **Note:** Replace `/absolute/path/to/ghidra_mcp_bridge/` with the actual path where you saved the file. If you are using a virtual environment (recommended), replace `"python3"` with the absolute path to your venv python executable (e.g., `"/path/to/venv/bin/python"`).

### 3. Configure Gemini CLI
You need to tell Gemini CLI how to launch this bridge. Open your Gemini CLI configuration file, which is typically found at `~/.gemini/settings.json` (user-level) or `.gemini/settings.json` (project-level).

Add the following entry to the `mcpServers` object:

```json
{
  "mcpServers": {
    "ghidra": {
      "command": "python3",
      "args": [
        "/absolute/path/to/ghidra_mcp_bridge/ghidra_mcp_sse_bridge.py"
      ]
    }
  }
}
```

> **Note:** Replace `/absolute/path/to/ghidra_mcp_bridge/` with the actual path where you saved the file. If you are using a virtual environment (recommended), replace `"python3"` with the absolute path to your venv python executable (e.g., `"/path/to/venv/bin/python"`).

### 4. Connect
Restart Claude Desktop or Gemini CLI. You should see a "ghidra" connection icon (plug) in the interface. You can now ask Claude (or Gemini CLI) to perform tasks in Ghidra, and it will use the tools provided by the GhidrAssistMCP plugin.

## Troubleshooting

*   **Connection Error:** If the bridge fails to connect, ensure Ghidra is running and the GhidrAssistMCP server is started. Check the logs (Claude Desktop or Gemini CLI usually logs stderr) for messages like `CONNECTION ERROR: Could not connect to http://127.0.0.1:8080/sse`.
*   **Port Conflicts:** If your Ghidra server is running on a different port, modify the `GHIDRA_SSE_URL` variable in `ghidra_mcp_sse_bridge.py` to match your setup.
