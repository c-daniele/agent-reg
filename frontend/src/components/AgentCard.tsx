import React from 'react';
import { Agent } from '../types/agent';
import { formatDistanceToNow } from 'date-fns';

interface AgentCardProps {
  agent: Agent;
  onEdit?: (agent: Agent) => void;
  onDelete?: (agentId: string) => void;
  onHeartbeat?: (agentId: string) => void;
  onViewInvoke?: (agentId: string) => void;
}

const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  onEdit,
  onDelete,
  onHeartbeat,
  onViewInvoke,
}) => {
  const isAlive = agent.last_heartbeat 
    ? new Date(agent.last_heartbeat).getTime() > Date.now() - 5 * 60 * 1000
    : false;

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return 'Invalid date';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              {agent.name || 'Unnamed Agent'}
            </h3>
            <div className={`w-2 h-2 rounded-full ${
              isAlive ? 'bg-green-400' : 'bg-gray-300'
            }`} title={isAlive ? 'Active' : 'Inactive'} />
          </div>
          
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
            {agent.description || 'No description available'}
          </p>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Version:</span>
              <span className="ml-1 text-gray-900">
                {agent.version || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Protocol:</span>
              <span className="ml-1 text-gray-900">
                {agent.protocolVersion || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Owner:</span>
              <span className="ml-1 text-gray-900">
                {agent.owner || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Skills:</span>
              <span className="ml-1 text-gray-900">
                {agent.skills?.length || 0}
              </span>
            </div>
          </div>

          <div className="mt-3 text-xs text-gray-500">
            Created: {formatDate(agent.created_at)}
            <br />
            Last heartbeat: {formatDate(agent.last_heartbeat)}
          </div>
        </div>

        <div className="flex flex-col gap-2 ml-4">
          {onViewInvoke && (
            <button
              onClick={() => onViewInvoke(agent.id)}
              className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded hover:bg-blue-200 transition-colors"
            >
              Invoke
            </button>
          )}
          {onHeartbeat && (
            <button
              onClick={() => onHeartbeat(agent.id)}
              className="px-3 py-1 text-xs font-medium text-green-700 bg-green-100 rounded hover:bg-green-200 transition-colors"
            >
              Heartbeat
            </button>
          )}
          {onEdit && (
            <button
              onClick={() => onEdit(agent)}
              className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
            >
              Edit
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(agent.id)}
              className="px-3 py-1 text-xs font-medium text-red-700 bg-red-100 rounded hover:bg-red-200 transition-colors"
            >
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentCard;