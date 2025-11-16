/**
 * TypeScript type definitions for MCP (Model Context Protocol) Gateway
 */

export type MCPServerType = 'stdio' | 'http' | 'sse';
export type MCPServerStatus = 'active' | 'inactive' | 'error';
export type MCPCapabilityType = 'tool' | 'resource' | 'prompt';

// MCP Tool Capability
export interface MCPToolCapability {
  name: string;
  description?: string;
  inputSchema?: Record<string, any>;
}

// MCP Resource Capability
export interface MCPResourceCapability {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

// MCP Prompt Capability
export interface MCPPromptArgument {
  name: string;
  description?: string;
  required?: boolean;
}

export interface MCPPromptCapability {
  name: string;
  description?: string;
  arguments?: MCPPromptArgument[];
}

// MCP Server Capabilities
export interface MCPServerCapabilities {
  tools?: MCPToolCapability[];
  resources?: MCPResourceCapability[];
  prompts?: MCPPromptCapability[];
}

// MCP Server Configuration (stored in DB)
export interface MCPServerConfig {
  // stdio config
  command?: string;
  args?: string[];
  env?: Record<string, string>;

  // http/sse config
  url?: string;
  headers?: Record<string, string>;
}

// MCP Server Registration Request
export interface MCPServerRegister {
  type: MCPServerType;
  description?: string;

  // stdio fields
  command?: string;
  args?: string[];
  env?: Record<string, string>;

  // http/sse fields
  url?: string;
  headers?: Record<string, string>;
}

// MCP Server Response (from API)
export interface MCPServer {
  id: string;
  type: MCPServerType;
  description?: string;
  config: MCPServerConfig;
  capabilities: MCPServerCapabilities;
  created_at: string;
  last_verified?: string;
  status: MCPServerStatus;
}

// MCP Search Query
export interface MCPSearchQuery {
  query?: string;
  capability_type?: MCPCapabilityType;
  server_type?: MCPServerType;
  limit?: number;
}

// MCP Search Result
export interface MCPSearchResult {
  server_id: string;
  server_type: MCPServerType;
  server_description?: string;
  server_config: MCPServerConfig;
  matched_tools?: MCPToolCapability[];
  matched_resources?: MCPResourceCapability[];
  matched_prompts?: MCPPromptCapability[];
  relevance_score?: number;
}

// MCP Verification Response
export interface MCPVerificationResponse {
  server_id: string;
  status: MCPServerStatus;
  message: string;
  capabilities?: MCPServerCapabilities;
}

// Gateway Types
export type ConnectionState = 'connected' | 'disconnected' | 'connecting' | 'error';

export interface ConnectionStatus {
  server_id: string;
  state: ConnectionState;
  connected_at?: string;
  last_activity?: string;
  error?: string;
}

export interface GatewayHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  total_connections: number;
  active_connections: number;
  failed_connections: number;
  connection_details: Record<string, ConnectionStatus>;
}

export interface JSONRPCRequest {
  jsonrpc: string;
  id?: string | number;
  method: string;
  params?: Record<string, any>;
}

export interface JSONRPCResponse {
  jsonrpc: string;
  id?: string | number;
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

export interface ToolCallRequest {
  arguments?: Record<string, any>;
}

export interface ToolCallResponse {
  content: Array<{
    type: string;
    text?: string;
    [key: string]: any;
  }>;
  isError?: boolean;
}

export interface ResourceReadRequest {
  uri: string;
}

export interface PromptGetRequest {
  name: string;
  arguments?: Record<string, any>;
}
