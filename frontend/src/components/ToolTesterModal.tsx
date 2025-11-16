import React, { useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon, PlayIcon, SignalIcon, SignalSlashIcon } from '@heroicons/react/24/outline';
import { MCPAPI } from '../services/api';
import { MCPServer, MCPToolCapability, ConnectionStatus } from '../types/mcp';

interface ToolTesterModalProps {
  isOpen: boolean;
  onClose: () => void;
  server: MCPServer;
}

const ToolTesterModal: React.FC<ToolTesterModalProps> = ({ isOpen, onClose, server }) => {
  const [selectedTool, setSelectedTool] = useState<MCPToolCapability | null>(null);
  const [toolArgs, setToolArgs] = useState<string>('{}');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);

  useEffect(() => {
    if (isOpen && server.capabilities.tools && server.capabilities.tools.length > 0) {
      setSelectedTool(server.capabilities.tools[0]);
      // Load initial connection status
      loadConnectionStatus();
    }
  }, [isOpen, server]);

  const loadConnectionStatus = async () => {
    setStatusLoading(true);
    try {
      const status = await MCPAPI.getConnectionStatus(server.id);
      setConnectionStatus(status);
    } catch (err: any) {
      console.error('Failed to load connection status:', err);
    } finally {
      setStatusLoading(false);
    }
  };

  const handleTestTool = async () => {
    if (!selectedTool) return;

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const args = JSON.parse(toolArgs);
      const response = await MCPAPI.callTool(server.id, selectedTool.name, { arguments: args });
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to call tool');
    } finally {
      setIsLoading(false);
    }
  };

  const getConnectionBadge = () => {
    if (statusLoading) {
      return (
        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-600">
          <SignalSlashIcon className="h-3 w-3 mr-1" />
          Loading...
        </span>
      );
    }

    if (!connectionStatus) {
      return (
        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-600">
          <SignalSlashIcon className="h-3 w-3 mr-1" />
          Unknown
        </span>
      );
    }

    const stateColors = {
      connected: 'bg-green-100 text-green-700',
      connecting: 'bg-yellow-100 text-yellow-700',
      disconnected: 'bg-gray-100 text-gray-700',
      error: 'bg-red-100 text-red-700'
    };

    return (
      <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${stateColors[connectionStatus.state]}`}>
        <SignalIcon className="h-3 w-3 mr-1" />
        {connectionStatus.state}
      </span>
    );
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <Dialog.Title as="h3" className="text-lg font-semibold text-gray-900">
                      Test Tools - {server.type.toUpperCase()} Server
                    </Dialog.Title>
                    <div className="mt-2 flex items-center space-x-2">
                      {getConnectionBadge()}
                      <button
                        onClick={loadConnectionStatus}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        Refresh
                      </button>
                    </div>
                  </div>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-500"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {/* Tool Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Tool
                  </label>
                  <select
                    value={selectedTool?.name || ''}
                    onChange={(e) => {
                      const tool = server.capabilities.tools?.find(t => t.name === e.target.value);
                      setSelectedTool(tool || null);
                      setResult(null);
                      setError('');
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {server.capabilities.tools?.map((tool) => (
                      <option key={tool.name} value={tool.name}>
                        {tool.name}
                      </option>
                    ))}
                  </select>
                  {selectedTool?.description && (
                    <p className="mt-2 text-sm text-gray-600">{selectedTool.description}</p>
                  )}
                </div>

                {/* Tool Arguments */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Arguments (JSON)
                  </label>
                  <textarea
                    value={toolArgs}
                    onChange={(e) => setToolArgs(e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder='{"key": "value"}'
                  />
                  {selectedTool?.inputSchema && (
                    <details className="mt-2">
                      <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">
                        View Input Schema
                      </summary>
                      <pre className="mt-2 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                        {JSON.stringify(selectedTool.inputSchema, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>

                {/* Test Button */}
                <button
                  onClick={handleTestTool}
                  disabled={isLoading || !selectedTool}
                  className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors mb-4"
                >
                  <PlayIcon className="h-4 w-4 mr-2" />
                  {isLoading ? 'Testing...' : 'Test Tool'}
                </button>

                {/* Error Display */}
                {error && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 className="text-sm font-semibold text-red-800 mb-2">Error</h4>
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                )}

                {/* Result Display */}
                {result && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-gray-800 mb-2">Result</h4>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-64 overflow-y-auto">
                      <pre className="text-xs font-mono whitespace-pre-wrap">
                        {JSON.stringify(result, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default ToolTesterModal;
