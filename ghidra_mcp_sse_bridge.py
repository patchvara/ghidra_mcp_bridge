import asyncio
import sys
import httpx
import traceback

# Import official MCP classes
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from mcp.types import (
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource,
    ServerCapabilities
)

# CONFIGURATION
GHIDRA_SSE_URL = "http://127.0.0.1:8080/sse"

async def main():
    print(f"🔌 Connecting to Ghidra SSE at {GHIDRA_SSE_URL}...", file=sys.stderr)

    try:
        # 1. Establish the SSE Connection to Ghidra
        async with sse_client(GHIDRA_SSE_URL) as (sse_read, sse_write):
            print("✅ SSE Transport Established.", file=sys.stderr)
            
            # 2. Initialize the Client Session (We act as a Client to Ghidra)
            async with ClientSession(sse_read, sse_write) as ghidra_client:
                await ghidra_client.initialize()
                
                # Fetch tools once to verify connection
                tools_list = await ghidra_client.list_tools()
                print(f"✅ Client Session Initialized! Proxying {len(tools_list.tools)} tools.", file=sys.stderr)

                # 3. Initialize the Server (We act as a Server to Claude)
                app = Server("Ghidra Bridge")

                # --- Define Proxy Handlers ---

                @app.list_tools()
                async def list_tools() -> list[Tool]:
                    try:
                        result = await ghidra_client.list_tools()
                        return result.tools
                    except Exception as e:
                        print(f"⚠️ Error listing tools: {e}", file=sys.stderr)
                        return []

                @app.call_tool()
                async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
                    print(f"➡️ Forwarding tool: {name}", file=sys.stderr)
                    try:
                        result = await ghidra_client.call_tool(name, arguments)
                        return result.content
                    except Exception as e:
                        print(f"❌ Tool Execution Error: {e}", file=sys.stderr)
                        return [TextContent(type="text", text=f"Error executing tool '{name}': {str(e)}")]

                # 4. Connect our Server to Claude via Stdio
                async with stdio_server() as (stdin, stdout):
                    print("🚀 Bridge is ready. Listening for Claude...", file=sys.stderr)
                    
                    # FIX: Construct InitializationOptions using the available import or a dict.
                    # This satisfies the requirement for the 3rd argument in app.run()
                    try:
                        # Try importing from server (newer SDK location)
                        from mcp.server import InitializationOptions
                        init_options = InitializationOptions(
                            server_name="ghidra-bridge",
                            server_version="1.0.0",
                            capabilities=ServerCapabilities(
                                tools={"listChanged": True},
                                prompts={},
                                resources={}
                            )
                        )
                    except ImportError:
                        # Fallback: Pass a dictionary (Pydantic will validate this automatically)
                        init_options = {
                            "server_name": "ghidra-bridge",
                            "server_version": "1.0.0",
                            "capabilities": {
                                "tools": {"listChanged": True},
                                "prompts": {},
                                "resources": {}
                            }
                        }

                    await app.run(stdin, stdout, init_options)

    except httpx.ConnectError:
        print(f"\n❌ CONNECTION ERROR: Could not connect to {GHIDRA_SSE_URL}", file=sys.stderr)
        print("   -> Is Ghidra running? Is the GhidrAssistMCP server started?", file=sys.stderr)
    
    except Exception as e:
        # Handle Python 3.11+ ExceptionGroups
        if sys.version_info >= (3, 11) and type(e).__name__ == "ExceptionGroup":
            print("\n❌ CRITICAL: Unhandled Exception Group caught!", file=sys.stderr)
            for i, exc in enumerate(e.exceptions):
                print(f"   [Sub-Exception {i+1}]: {type(exc).__name__} - {exc}", file=sys.stderr)
        else:
            print(f"\n❌ CRITICAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
