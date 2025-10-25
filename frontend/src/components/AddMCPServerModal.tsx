import React, { useState, Fragment } from 'react';
import { Dialog, Transition, Tab } from '@headlessui/react';
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import { MCPServerRegister, MCPServerType } from '../types/mcp';

interface AddMCPServerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (serverData: MCPServerRegister) => Promise<void>;
}

const AddMCPServerModal: React.FC<AddMCPServerModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [serverType, setServerType] = useState<MCPServerType>('stdio');
  const [description, setDescription] = useState('');

  // stdio fields
  const [command, setCommand] = useState('');
  const [args, setArgs] = useState('');
  const [envVars, setEnvVars] = useState<{ key: string; value: string }[]>([]);

  // http/sse fields
  const [url, setUrl] = useState('');
  const [headers, setHeaders] = useState<{ key: string; value: string }[]>([]);

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const resetForm = () => {
    setServerType('stdio');
    setDescription('');
    setCommand('');
    setArgs('');
    setEnvVars([]);
    setUrl('');
    setHeaders([]);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const serverData: MCPServerRegister = {
        type: serverType,
        description: description || undefined,
      };

      if (serverType === 'stdio') {
        if (!command.trim()) {
          throw new Error('Command is required for stdio servers');
        }
        serverData.command = command.trim();

        if (args.trim()) {
          serverData.args = args.trim().split(/\s+/);
        }

        if (envVars.length > 0) {
          serverData.env = envVars.reduce((acc, { key, value }) => {
            if (key.trim()) {
              acc[key.trim()] = value;
            }
            return acc;
          }, {} as Record<string, string>);
        }
      } else {
        // http or sse
        if (!url.trim()) {
          throw new Error('URL is required for HTTP/SSE servers');
        }
        serverData.url = url.trim();

        if (headers.length > 0) {
          serverData.headers = headers.reduce((acc, { key, value }) => {
            if (key.trim()) {
              acc[key.trim()] = value;
            }
            return acc;
          }, {} as Record<string, string>);
        }
      }

      await onSubmit(serverData);
      resetForm();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to register MCP server');
    } finally {
      setLoading(false);
    }
  };

  const addEnvVar = () => {
    setEnvVars([...envVars, { key: '', value: '' }]);
  };

  const removeEnvVar = (index: number) => {
    setEnvVars(envVars.filter((_, i) => i !== index));
  };

  const updateEnvVar = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...envVars];
    updated[index][field] = value;
    setEnvVars(updated);
  };

  const addHeader = () => {
    setHeaders([...headers, { key: '', value: '' }]);
  };

  const removeHeader = (index: number) => {
    setHeaders(headers.filter((_, i) => i !== index));
  };

  const updateHeader = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...headers];
    updated[index][field] = value;
    setHeaders(updated);
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
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
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 shadow-xl transition-all">
                <div className="flex justify-between items-start mb-6">
                  <Dialog.Title className="text-2xl font-bold text-gray-900">
                    Register MCP Server
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-500"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Server Type Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Server Type
                    </label>
                    <div className="flex space-x-4">
                      {(['stdio', 'http', 'sse'] as MCPServerType[]).map((type) => (
                        <button
                          key={type}
                          type="button"
                          onClick={() => setServerType(type)}
                          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                            serverType === type
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          {type.toUpperCase()}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description (Optional)
                    </label>
                    <input
                      type="text"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="e.g., Weather information server"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  {/* stdio Configuration */}
                  {serverType === 'stdio' && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Command <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={command}
                          onChange={(e) => setCommand(e.target.value)}
                          placeholder="e.g., python3 or node"
                          required
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Arguments (space-separated)
                        </label>
                        <input
                          type="text"
                          value={args}
                          onChange={(e) => setArgs(e.target.value)}
                          placeholder="e.g., -m mcp_server"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>

                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="block text-sm font-medium text-gray-700">
                            Environment Variables
                          </label>
                          <button
                            type="button"
                            onClick={addEnvVar}
                            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                          >
                            + Add Variable
                          </button>
                        </div>
                        {envVars.map((envVar, index) => (
                          <div key={index} className="flex space-x-2 mb-2">
                            <input
                              type="text"
                              value={envVar.key}
                              onChange={(e) => updateEnvVar(index, 'key', e.target.value)}
                              placeholder="KEY"
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            />
                            <input
                              type="text"
                              value={envVar.value}
                              onChange={(e) => updateEnvVar(index, 'value', e.target.value)}
                              placeholder="value"
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            />
                            <button
                              type="button"
                              onClick={() => removeEnvVar(index)}
                              className="px-3 py-2 text-red-600 hover:text-red-700"
                            >
                              <XMarkIcon className="h-5 w-5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </>
                  )}

                  {/* HTTP/SSE Configuration */}
                  {(serverType === 'http' || serverType === 'sse') && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          URL <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="url"
                          value={url}
                          onChange={(e) => setUrl(e.target.value)}
                          placeholder="e.g., http://localhost:3000/mcp"
                          required
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>

                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="block text-sm font-medium text-gray-700">
                            HTTP Headers
                          </label>
                          <button
                            type="button"
                            onClick={addHeader}
                            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                          >
                            + Add Header
                          </button>
                        </div>
                        {headers.map((header, index) => (
                          <div key={index} className="flex space-x-2 mb-2">
                            <input
                              type="text"
                              value={header.key}
                              onChange={(e) => updateHeader(index, 'key', e.target.value)}
                              placeholder="Header-Name"
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            />
                            <input
                              type="text"
                              value={header.value}
                              onChange={(e) => updateHeader(index, 'value', e.target.value)}
                              placeholder="value"
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            />
                            <button
                              type="button"
                              onClick={() => removeHeader(index)}
                              className="px-3 py-2 text-red-600 hover:text-red-700"
                            >
                              <XMarkIcon className="h-5 w-5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </>
                  )}

                  {/* Error Message */}
                  {error && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">{error}</p>
                    </div>
                  )}

                  {/* Submit Buttons */}
                  <div className="flex space-x-4 pt-4">
                    <button
                      type="button"
                      onClick={onClose}
                      className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? 'Registering...' : 'Register Server'}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default AddMCPServerModal;
