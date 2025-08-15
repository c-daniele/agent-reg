import axios from 'axios';
import {
  Agent,
  AgentCard,
  AgentUpdate,
  AgentListParams,
  AgentInvokeResponse,
  HealthResponse
} from '../types/agent';

// Base API URL - can be configured via environment variables
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service class for Agent2Agent registry
export class AgentAPI {
  
  // Register a new agent
  static async registerAgent(agentCard: AgentCard): Promise<Agent> {
    const response = await apiClient.post<Agent>('/agents/register', agentCard);
    return response.data;
  }

  // List and search agents
  static async listAgents(params?: AgentListParams): Promise<Agent[]> {
    const response = await apiClient.get<Agent[]>('/agents', { params });
    return response.data;
  }

  // Get a specific agent by ID
  static async getAgent(agentId: string): Promise<Agent> {
    const response = await apiClient.get<Agent>(`/agents/${agentId}`);
    return response.data;
  }

  // Update an agent
  static async updateAgent(agentId: string, update: AgentUpdate): Promise<Agent> {
    const response = await apiClient.put<Agent>(`/agents/${agentId}`, update);
    return response.data;
  }

  // Delete an agent
  static async deleteAgent(agentId: string): Promise<void> {
    await apiClient.delete(`/agents/${agentId}`);
  }

  // Update agent heartbeat
  static async updateHeartbeat(agentId: string): Promise<Agent> {
    const response = await apiClient.post<Agent>(`/agents/${agentId}/heartbeat`);
    return response.data;
  }

  // Get agent invocation URL
  static async getAgentInvokeUrl(agentId: string): Promise<AgentInvokeResponse> {
    const response = await apiClient.get<AgentInvokeResponse>(`/agents/${agentId}/invoke_url`);
    return response.data;
  }

  // Health check
  static async healthCheck(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/health');
    return response.data;
  }
}

export default AgentAPI;