#!/usr/bin/env python3
"""
Simple Example MCP Server (stdio)

This is a minimal MCP server that demonstrates the protocol.
It exposes a few example tools, resources, and prompts.

Usage:
    python simple_mcp_server.py
"""

import sys
import json
import logging

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class SimpleMCPServer:
    """Simple MCP Server implementation"""

    def __init__(self):
        self.server_info = {
            "name": "simple-mcp-server",
            "version": "1.0.0"
        }
        self.capabilities = {
            "tools": {},
            "resources": {},
            "prompts": {}
        }

    def handle_initialize(self, params):
        """Handle initialize request"""
        logger.info("Received initialize request")
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": self.server_info,
            "capabilities": self.capabilities
        }

    def handle_tools_list(self, params):
        """Handle tools/list request"""
        logger.info("Received tools/list request")
        return {
            "tools": [
                {
                    "name": "echo",
                    "description": "Echo back the input message",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Message to echo"
                            }
                        },
                        "required": ["message"]
                    }
                },
                {
                    "name": "add",
                    "description": "Add two numbers together",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"}
                        },
                        "required": ["a", "b"]
                    }
                },
                {
                    "name": "greet",
                    "description": "Generate a greeting message",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name to greet"}
                        },
                        "required": ["name"]
                    }
                }
            ]
        }

    def handle_resources_list(self, params):
        """Handle resources/list request"""
        logger.info("Received resources/list request")
        return {
            "resources": [
                {
                    "uri": "file://config.json",
                    "name": "Configuration",
                    "description": "Server configuration file",
                    "mimeType": "application/json"
                },
                {
                    "uri": "file://data/sample.txt",
                    "name": "Sample Data",
                    "description": "Sample text data",
                    "mimeType": "text/plain"
                }
            ]
        }

    def handle_prompts_list(self, params):
        """Handle prompts/list request"""
        logger.info("Received prompts/list request")
        return {
            "prompts": [
                {
                    "name": "summarize",
                    "description": "Summarize a given text",
                    "arguments": [
                        {
                            "name": "text",
                            "description": "Text to summarize",
                            "required": True
                        }
                    ]
                },
                {
                    "name": "translate",
                    "description": "Translate text to another language",
                    "arguments": [
                        {
                            "name": "text",
                            "description": "Text to translate",
                            "required": True
                        },
                        {
                            "name": "target_language",
                            "description": "Target language code",
                            "required": True
                        }
                    ]
                }
            ]
        }

    def handle_request(self, request):
        """Handle incoming JSON-RPC request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        logger.info(f"Handling request: {method}")

        # Handle methods
        if method == "initialize":
            result = self.handle_initialize(params)
        elif method == "tools/list":
            result = self.handle_tools_list(params)
        elif method == "resources/list":
            result = self.handle_resources_list(params)
        elif method == "prompts/list":
            result = self.handle_prompts_list(params)
        elif method == "notifications/initialized":
            # No response for notifications
            return None
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    def run(self):
        """Run the server (stdio mode)"""
        logger.info("Starting Simple MCP Server (stdio mode)")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    logger.info(f"Received request: {request.get('method')}")

                    response = self.handle_request(request)
                    if response:
                        # Write response to stdout
                        sys.stdout.write(json.dumps(response) + "\n")
                        sys.stdout.flush()

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)


if __name__ == "__main__":
    server = SimpleMCPServer()
    server.run()
