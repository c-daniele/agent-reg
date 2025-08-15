from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl


# --- Models ---
class AgentExtension(BaseModel):
    """A declaration of a protocol extension supported by an Agent."""
    uri: str = Field(..., description="The unique URI identifying the extension.")
    description: Optional[str] = Field(None, description="A human-readable description of how this agent uses the extension.")
    required: Optional[bool] = Field(None, description="If true, the client must understand and comply with the extension's requirements to interact with the agent.")
    params: Optional[Dict[str, Any]] = Field(None, description="Optional, extension-specific configuration parameters.")


class AgentCapabilities(BaseModel):
    """Defines optional capabilities supported by an agent."""
    streaming: Optional[bool] = Field(None, description="Indicates if the agent supports Server-Sent Events (SSE) for streaming responses.")
    stateTransitionHistory: Optional[bool] = Field(None, description="Indicates if the agent provides a history of state transitions for a task.")
    pushNotifications: Optional[bool] = Field(None, description="Indicates if the agent supports sending push notifications for asynchronous task updates.")
    extensions: Optional[List[AgentExtension]] = Field(None, description="A list of protocol extensions supported by the agent.")


class AgentProvider(BaseModel):
    """Represents the service provider of an agent."""
    organization: str = Field(..., description="The name of the agent provider's organization.")
    url: str = Field(..., description="A URL for the agent provider's website or relevant documentation.")


class AgentInterface(BaseModel):
    """Declares a combination of a target URL and a transport protocol for interacting with the agent."""
    url: str = Field(..., description="The URL where this interface is available.")
    transport: str = Field(..., description="The transport protocol supported at this URL.")


class AgentCardSignature(BaseModel):
    """AgentCardSignature represents a JWS signature of an AgentCard."""
    protected: str = Field(..., description="The protected JWS header for the signature.")
    signature: str = Field(..., description="The computed signature, Base64url-encoded.")
    header: Optional[Dict[str, Any]] = Field(None, description="The unprotected JWS header values.")


class AgentSkill(BaseModel):
    """Represents a distinct capability or function that an agent can perform."""
    id: str = Field(..., description="A unique identifier for the agent's skill.")
    name: str = Field(..., description="A human-readable name for the skill.")
    description: str = Field(..., description="A detailed description of the skill, intended to help clients or users understand its purpose and functionality.")
    tags: List[str] = Field(..., description="A set of keywords describing the skill's capabilities.")
    
    examples: Optional[List[str]] = Field(None, description="Example prompts or scenarios that this skill can handle.")
    inputModes: Optional[List[str]] = Field(None, description="The set of supported input MIME types for this skill, overriding the agent's defaults.")
    outputModes: Optional[List[str]] = Field(None, description="The set of supported output MIME types for this skill, overriding the agent's defaults.")
    security: Optional[List[Dict[str, List[str]]]] = Field(None, description="Security schemes necessary for the agent to leverage this skill.")


class AgentCard(BaseModel):
    """
    The AgentCard is a self-describing manifest for an agent. It provides essential
    metadata including the agent's identity, capabilities, skills, supported
    communication methods, and security requirements.
    """
    name: str = Field(..., description="A human-readable name for the agent.")
    description: str = Field(..., description="A human-readable description of the agent, assisting users and other agents in understanding its purpose.")
    version: str = Field(..., description="The agent's own version number. The format is defined by the provider.")
    protocolVersion: str = Field(..., description="The version of the A2A protocol this agent supports.")
    url: str = Field(..., description="The preferred endpoint URL for interacting with the agent.")
    skills: List[AgentSkill] = Field(..., description="The set of skills, or distinct capabilities, that the agent can perform.")
    capabilities: AgentCapabilities = Field(..., description="A declaration of optional capabilities supported by the agent.")
    defaultInputModes: List[str] = Field(..., description="Default set of supported input MIME types for all skills.")
    defaultOutputModes: List[str] = Field(..., description="Default set of supported output MIME types for all skills.")
    
    # Optional fields
    preferredTransport: Optional[str] = Field("JSONRPC", description="The transport protocol for the preferred endpoint.")
    provider: Optional[AgentProvider] = Field(None, description="Information about the agent's service provider.")
    documentationUrl: Optional[str] = Field(None, description="An optional URL to the agent's documentation.")
    iconUrl: Optional[str] = Field(None, description="An optional URL to an icon for the agent.")
    additionalInterfaces: Optional[List[AgentInterface]] = Field(None, description="A list of additional supported interfaces.")
    security: Optional[List[Dict[str, List[str]]]] = Field(None, description="A list of security requirement objects that apply to all agent interactions.")
    securitySchemes: Optional[Dict[str, Any]] = Field(None, description="A declaration of the security schemes available to authorize requests.")
    signatures: Optional[List[AgentCardSignature]] = Field(None, description="JSON Web Signatures computed for this AgentCard.")
    supportsAuthenticatedExtendedCard: Optional[bool] = Field(None, description="If true, the agent can provide an extended agent card with additional details to authenticated users.")


class AgentCreate(AgentCard):
    owner: Optional[str] = Field("root", description="The owner of the agent. This is used for ownership tracking and management.")

class AgentUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    url: Optional[HttpUrl]
    version: Optional[str]
    protocolVersion: Optional[str]
    capabilities: Optional[Dict[str, Any]]
    skills: Optional[List[AgentSkill]]
