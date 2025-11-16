import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { MCPServer } from '../types/mcp';
import {
  ServerIcon,
  CommandLineIcon,
  GlobeAltIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  WrenchIcon,
  DocumentTextIcon,
  ChatBubbleBottomCenterTextIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';
import ToolTesterModal from './ToolTesterModal';

interface MCPServerCardProps {
  server: MCPServer;
  onDelete: (serverId: string) => void;
  onVerify: (serverId: string) => void;
}

const MCPServerCard: React.FC<MCPServerCardProps> = ({ server, onDelete, onVerify }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [showResources, setShowResources] = useState(false);
  const [showPrompts, setShowPrompts] = useState(false);
  const [showToolTester, setShowToolTester] = useState(false);

  const getStatusColor = () => {
    switch (server.status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'inactive':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getTypeIcon = () => {
    switch (server.type) {
      case 'stdio':
        return <CommandLineIcon className="h-5 w-5" />;
      case 'http':
      case 'sse':
        return <GlobeAltIcon className="h-5 w-5" />;
      default:
        return <ServerIcon className="h-5 w-5" />;
    }
  };

  const toolsCount = server.capabilities?.tools?.length || 0;
  const resourcesCount = server.capabilities?.resources?.length || 0;
  const promptsCount = server.capabilities?.prompts?.length || 0;

  return (
    <div className="bg-white shadow-md rounded-lg p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            {getTypeIcon()}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {server.type.toUpperCase()} Server
            </h3>
            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor()}`}>
              {server.status}
            </span>
          </div>
        </div>
      </div>

      {/* Description */}
      {server.description && (
        <p className="text-sm text-gray-600 mb-4">{server.description}</p>
      )}

      {/* Capability Summary */}
      <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <WrenchIcon className="h-4 w-4 text-blue-600 mr-1" />
            <span className="text-lg font-bold text-gray-900">{toolsCount}</span>
          </div>
          <span className="text-xs text-gray-600">Tools</span>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <DocumentTextIcon className="h-4 w-4 text-green-600 mr-1" />
            <span className="text-lg font-bold text-gray-900">{resourcesCount}</span>
          </div>
          <span className="text-xs text-gray-600">Resources</span>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <ChatBubbleBottomCenterTextIcon className="h-4 w-4 text-purple-600 mr-1" />
            <span className="text-lg font-bold text-gray-900">{promptsCount}</span>
          </div>
          <span className="text-xs text-gray-600">Prompts</span>
        </div>
      </div>

      {/* Timestamps */}
      <div className="text-xs text-gray-500 mb-4 space-y-1">
        <div>Created: {formatDistanceToNow(new Date(server.created_at), { addSuffix: true })}</div>
        {server.last_verified && (
          <div>Last verified: {formatDistanceToNow(new Date(server.last_verified), { addSuffix: true })}</div>
        )}
      </div>

      {/* Toggle Details Button */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="w-full flex items-center justify-between px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors mb-4"
      >
        <span>{showDetails ? 'Hide Details' : 'Show Details'}</span>
        {showDetails ? (
          <ChevronUpIcon className="h-4 w-4" />
        ) : (
          <ChevronDownIcon className="h-4 w-4" />
        )}
      </button>

      {/* Details Panel */}
      {showDetails && (
        <div className="space-y-4 mb-4 p-4 bg-gray-50 rounded-lg">
          {/* Configuration */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Configuration</h4>
            <div className="text-xs text-gray-600 space-y-1 font-mono bg-white p-3 rounded">
              {server.type === 'stdio' && (
                <>
                  <div><span className="font-semibold">Command:</span> {server.config.command}</div>
                  {server.config.args && server.config.args.length > 0 && (
                    <div><span className="font-semibold">Args:</span> {server.config.args.join(' ')}</div>
                  )}
                </>
              )}
              {(server.type === 'http' || server.type === 'sse') && (
                <div><span className="font-semibold">URL:</span> {server.config.url}</div>
              )}
            </div>
          </div>

          {/* Tools */}
          {toolsCount > 0 && (
            <div>
              <button
                onClick={() => setShowTools(!showTools)}
                className="flex items-center justify-between w-full text-sm font-semibold text-gray-700 mb-2"
              >
                <div className="flex items-center">
                  <WrenchIcon className="h-4 w-4 mr-2 text-blue-600" />
                  Tools ({toolsCount})
                </div>
                {showTools ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
              </button>
              {showTools && (
                <div className="space-y-2">
                  {server.capabilities.tools?.map((tool, idx) => (
                    <div key={idx} className="p-3 bg-white rounded border border-blue-200">
                      <div className="font-semibold text-sm text-blue-900">{tool.name}</div>
                      {tool.description && (
                        <div className="text-xs text-gray-600 mt-1">{tool.description}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Resources */}
          {resourcesCount > 0 && (
            <div>
              <button
                onClick={() => setShowResources(!showResources)}
                className="flex items-center justify-between w-full text-sm font-semibold text-gray-700 mb-2"
              >
                <div className="flex items-center">
                  <DocumentTextIcon className="h-4 w-4 mr-2 text-green-600" />
                  Resources ({resourcesCount})
                </div>
                {showResources ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
              </button>
              {showResources && (
                <div className="space-y-2">
                  {server.capabilities.resources?.map((resource, idx) => (
                    <div key={idx} className="p-3 bg-white rounded border border-green-200">
                      <div className="font-semibold text-sm text-green-900">{resource.name}</div>
                      <div className="text-xs text-gray-500 font-mono mt-1">{resource.uri}</div>
                      {resource.description && (
                        <div className="text-xs text-gray-600 mt-1">{resource.description}</div>
                      )}
                      {resource.mimeType && (
                        <div className="text-xs text-gray-500 mt-1">Type: {resource.mimeType}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Prompts */}
          {promptsCount > 0 && (
            <div>
              <button
                onClick={() => setShowPrompts(!showPrompts)}
                className="flex items-center justify-between w-full text-sm font-semibold text-gray-700 mb-2"
              >
                <div className="flex items-center">
                  <ChatBubbleBottomCenterTextIcon className="h-4 w-4 mr-2 text-purple-600" />
                  Prompts ({promptsCount})
                </div>
                {showPrompts ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
              </button>
              {showPrompts && (
                <div className="space-y-2">
                  {server.capabilities.prompts?.map((prompt, idx) => (
                    <div key={idx} className="p-3 bg-white rounded border border-purple-200">
                      <div className="font-semibold text-sm text-purple-900">{prompt.name}</div>
                      {prompt.description && (
                        <div className="text-xs text-gray-600 mt-1">{prompt.description}</div>
                      )}
                      {prompt.arguments && prompt.arguments.length > 0 && (
                        <div className="text-xs text-gray-500 mt-2">
                          Arguments: {prompt.arguments.map(arg => arg.name).join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-2">
        {toolsCount > 0 && (
          <button
            onClick={() => setShowToolTester(true)}
            className="flex-1 flex items-center justify-center px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors"
          >
            <BeakerIcon className="h-4 w-4 mr-2" />
            Test Tools
          </button>
        )}
        <button
          onClick={() => onVerify(server.id)}
          className="flex-1 flex items-center justify-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <CheckCircleIcon className="h-4 w-4 mr-2" />
          Verify
        </button>
        <button
          onClick={() => {
            if (window.confirm('Are you sure you want to delete this MCP server?')) {
              onDelete(server.id);
            }
          }}
          className="flex items-center justify-center px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors"
        >
          <TrashIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Tool Tester Modal */}
      <ToolTesterModal
        isOpen={showToolTester}
        onClose={() => setShowToolTester(false)}
        server={server}
      />
    </div>
  );
};

export default MCPServerCard;
