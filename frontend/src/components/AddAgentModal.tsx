import React, { useState } from 'react';
import { AgentCard } from '../types/agent';
import AgentAPI from '../services/api';

interface AddAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAgentAdded: () => void;
}

type InputMethod = 'file' | 'uri';

const AddAgentModal: React.FC<AddAgentModalProps> = ({ isOpen, onClose, onAgentAdded }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inputMethod, setInputMethod] = useState<InputMethod>('file');
  const [wellKnownUri, setWellKnownUri] = useState('');
  const [agentCard, setAgentCard] = useState<AgentCard | null>(null);
  const [jsonPreview, setJsonPreview] = useState('');

  const validateAgentCard = (data: any): AgentCard => {
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid JSON format');
    }

    if (!data.name || typeof data.name !== 'string') {
      throw new Error('Agent name is required and must be a string');
    }

    if (!data.description || typeof data.description !== 'string') {
      throw new Error('Agent description is required and must be a string');
    }

    if (!data.url || typeof data.url !== 'string') {
      throw new Error('Agent URL is required and must be a string');
    }

    if (!data.version || typeof data.version !== 'string') {
      throw new Error('Agent version is required and must be a string');
    }

    if (!data.protocolVersion || typeof data.protocolVersion !== 'string') {
      throw new Error('Protocol version is required and must be a string');
    }

    if (!Array.isArray(data.skills)) {
      throw new Error('Skills must be an array');
    }

    if (!Array.isArray(data.defaultInputModes)) {
      throw new Error('defaultInputModes must be an array');
    }

    if (!Array.isArray(data.defaultOutputModes)) {
      throw new Error('defaultOutputModes must be an array');
    }

    return data as AgentCard;
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setError(null);
      const text = await file.text();
      const parsedJson = JSON.parse(text);
      const validatedCard = validateAgentCard(parsedJson);
      
      setAgentCard(validatedCard);
      setJsonPreview(JSON.stringify(validatedCard, null, 2));
    } catch (err: any) {
      setError(`Error reading file: ${err.message}`);
      setAgentCard(null);
      setJsonPreview('');
    }
  };

  const fetchFromUri = async () => {
    if (!wellKnownUri.trim()) {
      setError('Please enter a valid .well-known URI');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(wellKnownUri.trim());
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const validatedCard = validateAgentCard(data);
      
      setAgentCard(validatedCard);
      setJsonPreview(JSON.stringify(validatedCard, null, 2));
    } catch (err: any) {
      setError(`Error fetching URI: ${err.message}`);
      setAgentCard(null);
      setJsonPreview('');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!agentCard) {
      setError('Please upload a JSON file or fetch from a URI first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await AgentAPI.registerAgent(agentCard);
      onAgentAdded();
      onClose();
      resetForm();
    } catch (err: any) {
      console.error('Failed to register agent:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to register agent');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setInputMethod('file');
    setWellKnownUri('');
    setAgentCard(null);
    setJsonPreview('');
    setError(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Add New Agent</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-4">
                Choose how to add your agent:
              </label>
              <div className="flex space-x-4 mb-6">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="file"
                    checked={inputMethod === 'file'}
                    onChange={(e) => setInputMethod(e.target.value as InputMethod)}
                    className="form-radio text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Upload JSON file</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="uri"
                    checked={inputMethod === 'uri'}
                    onChange={(e) => setInputMethod(e.target.value as InputMethod)}
                    className="form-radio text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Fetch from .well-known URI</span>
                </label>
              </div>
            </div>

            {inputMethod === 'file' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload AgentCard JSON file
                </label>
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileUpload}
                  className="block w-full text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-md file:border-0
                    file:text-sm file:font-medium
                    file:bg-blue-50 file:text-blue-700
                    hover:file:bg-blue-100
                    focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Select a JSON file containing your AgentCard configuration
                </p>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  .well-known URI
                </label>
                <div className="flex space-x-2">
                  <input
                    type="url"
                    value={wellKnownUri}
                    onChange={(e) => setWellKnownUri(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="https://example.com/.well-known/agent-card"
                  />
                  <button
                    type="button"
                    onClick={fetchFromUri}
                    disabled={loading || !wellKnownUri.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Fetching...' : 'Fetch'}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Enter the URL where your AgentCard is published (e.g., /.well-known/agent-card)
                </p>
              </div>
            )}

            {jsonPreview && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Agent Card Preview
                </label>
                <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">
                      {agentCard?.name} - {agentCard?.version}
                    </span>
                    <span className="text-xs text-gray-500">
                      {agentCard?.skills?.length || 0} skill(s)
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{agentCard?.description}</p>
                  <details className="text-sm">
                    <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                      View full JSON
                    </summary>
                    <pre className="mt-2 p-3 bg-white border rounded text-xs overflow-auto max-h-60">
                      {jsonPreview}
                    </pre>
                  </details>
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Registering...' : 'Register Agent'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AddAgentModal;