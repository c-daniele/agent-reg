import React, { useState } from 'react';
import { AgentListParams } from '../types/agent';

interface AgentFiltersProps {
  onFiltersChange: (filters: AgentListParams) => void;
  loading?: boolean;
}

const AgentFilters: React.FC<AgentFiltersProps> = ({ onFiltersChange, loading }) => {
  const [filters, setFilters] = useState<AgentListParams>({});

  const handleFilterChange = (key: keyof AgentListParams, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearFilters = () => {
    setFilters({});
    onFiltersChange({});
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Name
          </label>
          <input
            type="text"
            value={filters.name || ''}
            onChange={(e) => handleFilterChange('name', e.target.value)}
            placeholder="Search by name"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Owner
          </label>
          <input
            type="text"
            value={filters.owner || ''}
            onChange={(e) => handleFilterChange('owner', e.target.value)}
            placeholder="Filter by owner"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Skill ID
          </label>
          <input
            type="text"
            value={filters.skill || ''}
            onChange={(e) => handleFilterChange('skill', e.target.value)}
            placeholder="Filter by skill ID"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Capabilities
          </label>
          <div className="space-y-2">
            {['push_notifications', 'streaming', 'state_transition_history'].map((capability) => (
                <label key={capability} className="flex items-center">
                <input
                  type="checkbox"
                  checked={
                  ((filters.capabilities || '')
                    .split(',')
                    .map(c => c.trim())
                    .filter(Boolean)
                  ).includes(capability)
                  }
                  onChange={(e) => {
                  const currentCapabilities = (filters.capabilities || '')
                    .split(',')
                    .map(c => c.trim())
                    .filter(Boolean);
                  let newCapabilities: string[];
                  if (e.target.checked) {
                    newCapabilities = [...currentCapabilities, capability];
                  } else {
                    newCapabilities = currentCapabilities.filter(c => c !== capability);
                  }
                  handleFilterChange('capabilities', newCapabilities.join(','));
                  }}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  disabled={loading}
                />
                <span className="ml-2 text-sm text-gray-700">
                  {capability.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
                </label>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.only_alive || false}
              onChange={(e) => handleFilterChange('only_alive', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              disabled={loading}
            />
            <span className="ml-2 text-sm text-gray-700">Only active agents</span>
          </label>
        </div>
      </div>

      <div className="flex justify-end mt-4">
        <button
          onClick={clearFilters}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
        >
          Clear Filters
        </button>
      </div>
    </div>
  );
};

export default AgentFilters;