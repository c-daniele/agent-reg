import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import AgentCard from './components/AgentCard';
import AgentFilters from './components/AgentFilters';
import AddAgentModal from './components/AddAgentModal';
import AgentAPI from './services/api';
import { Agent, AgentListParams } from './types/agent';

const App: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<AgentListParams>({});
  const [showAddModal, setShowAddModal] = useState(false);

  // Load agents on component mount and when filters change
  useEffect(() => {
    loadAgents();
  }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await AgentAPI.listAgents(filters);
      setAgents(data);
    } catch (err) {
      console.error('Failed to load agents:', err);
      setError('Failed to load agents. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleFiltersChange = (newFilters: AgentListParams) => {
    setFilters(newFilters);
  };

  const handleEdit = (agent: Agent) => {
    // TODO: Implement edit modal/form
    console.log('Edit agent:', agent);
    alert('Edit functionality will be implemented in the next phase');
  };

  const handleDelete = async (agentId: string) => {
    if (!window.confirm('Are you sure you want to delete this agent?')) {
      return;
    }

    try {
      await AgentAPI.deleteAgent(agentId);
      setAgents(agents.filter(agent => agent.id !== agentId));
    } catch (err) {
      console.error('Failed to delete agent:', err);
      alert('Failed to delete agent');
    }
  };

  const handleHeartbeat = async (agentId: string) => {
    try {
      const updatedAgent = await AgentAPI.updateHeartbeat(agentId);
      setAgents(agents.map(agent => 
        agent.id === agentId ? updatedAgent : agent
      ));
    } catch (err) {
      console.error('Failed to update heartbeat:', err);
      alert('Failed to update heartbeat');
    }
  };

  const handleViewInvoke = async (agentId: string) => {
    try {
      const invokeData = await AgentAPI.getAgentInvokeUrl(agentId);
      alert(`Agent Invoke URL:\n${invokeData.invoke_url}\n\nNote: ${invokeData.note}`);
    } catch (err) {
      console.error('Failed to get invoke URL:', err);
      alert('Failed to get invoke URL');
    }
  };

  const handleAddAgent = () => {
    setShowAddModal(true);
  };

  const handleCloseAddModal = () => {
    setShowAddModal(false);
  };

  const handleAgentAdded = () => {
    loadAgents(); // Refresh the agents list
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Agent Registry</h2>
            <p className="mt-2 text-gray-600">
              Manage your Agent2Agent compliant agents
            </p>
          </div>
          <button 
            onClick={handleAddAgent}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Add New Agent
          </button>
        </div>

        <AgentFilters 
          onFiltersChange={handleFiltersChange}
          loading={loading}
        />

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {loading && (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="text-sm text-gray-600 mb-4">
              Found {agents.length} agent{agents.length !== 1 ? 's' : ''}
            </div>

            {agents.length === 0 ? (
              <div className="text-center py-12">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No agents found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by registering your first agent.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onHeartbeat={handleHeartbeat}
                    onViewInvoke={handleViewInvoke}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <AddAgentModal
        isOpen={showAddModal}
        onClose={handleCloseAddModal}
        onAgentAdded={handleAgentAdded}
      />
    </Layout>
  );
};

export default App;