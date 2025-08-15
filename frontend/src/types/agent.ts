// Generated types based on OpenAPI spec for Agent2Agent API

export interface AgentExtension {
  uri: string;
  description?: string;
  required?: boolean;
  params?: Record<string, any>;
}

export interface AgentCapabilities {
  streaming?: boolean;
  stateTransitionHistory?: boolean;
  pushNotifications?: boolean;
  extensions?: AgentExtension[];
}

export interface AgentProvider {
  organization: string;
  url: string;
}

export interface AgentInterface {
  url: string;
  transport: string;
}

export interface AgentCardSignature {
  protected: string;
  signature: string;
  header?: Record<string, any>;
}

export interface AgentSkill {
  id: string;
  name: string;
  description: string;
  tags: string[];
  examples?: string[];
  inputModes?: string[];
  outputModes?: string[];
  security?: Array<Record<string, string[]>>;
}

export interface AgentCard {
  
  name: string;
  description: string;
  version: string;
  protocolVersion: string;
  url: string;
  skills: AgentSkill[];
  capabilities: AgentCapabilities;
  defaultInputModes: string[];
  defaultOutputModes: string[];
  preferredTransport?: string;

  provider?: AgentProvider;
  // example: {"organization": "Example Geo Services Inc.","url": "https://www.examplegeoservices.com"}

  documentationUrl?: string;
  iconUrl?: string;
  additionalInterfaces?: AgentInterface[];
  //example [{"transport": "GRPC", "url": "https://grpc.example.com/a2a"}]
  
  security?: Array<Record<string, string[]>>;
  /* examples:
  [{ "google": ["openid", "profile", "email"] }
    , {"oauth": ["read"]}
    , {"api-key": []}
    , {"mtls": []}
  ]
  */

  securitySchemes?: Record<string, any>;
  // example: [{"google": {"type": "openIdConnect","openIdConnectUrl": "https://accounts.google.com/.well-known/openid-configuration"}}]

  signatures?: AgentCardSignature[];
  supportsAuthenticatedExtendedCard?: boolean;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  url?: string;
  version?: string;
  protocolVersion?: string;
  capabilities?: Record<string, any>;
  skills?: AgentSkill[];
}

export interface Agent {
  id: string;
  name?: string;
  description?: string;
  url: string;
  version?: string;
  protocolVersion?: string;
  capabilities?: Record<string, any>;
  skills?: Record<string, any>[];
  owner?: string;
  created_at?: string;
  last_heartbeat?: string;
}

export interface ValidationError {
  loc?: string[];
  msg?: string;
  type?: string;
}

export interface HTTPValidationError {
  detail?: string | ValidationError[];
}

// API Response types
export interface AgentListParams {
  skill?: string;
  name?: string;
  owner?: string;

  // comma separated list of capabilities
  capabilities?: string;
  only_alive?: boolean;
}

export interface AgentInvokeResponse {
  agent_id: string;
  invoke_url: string;
  note: string;
  agent_card: Record<string, any>;
}

export interface HealthResponse {
  status: string;
  time: string;
}