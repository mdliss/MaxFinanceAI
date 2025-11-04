'use client'

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { User } from '@/types';

interface UserSearchProps {
  onUserSelect: (userId: string | null) => void;
  selectedUserId: string | null;
}

export default function UserSearch({ onUserSelect, selectedUserId }: UserSearchProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getUsers();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter((user) =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.user_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedUser = users.find((u) => u.user_id === selectedUserId);

  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <div className="relative">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Search Users
        </label>
        <div className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setShowDropdown(true);
            }}
            onFocus={() => setShowDropdown(true)}
            placeholder="Search by name or user ID..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {selectedUser && (
            <button
              onClick={() => {
                onUserSelect(null);
                setSearchTerm('');
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          )}
        </div>

        {/* Dropdown */}
        {showDropdown && searchTerm && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
            {loading ? (
              <div className="px-4 py-3 text-sm text-gray-500">Loading...</div>
            ) : error ? (
              <div className="px-4 py-3 text-sm text-red-600">{error}</div>
            ) : filteredUsers.length === 0 ? (
              <div className="px-4 py-3 text-sm text-gray-500">No users found</div>
            ) : (
              filteredUsers.map((user) => (
                <button
                  key={user.user_id}
                  onClick={() => {
                    onUserSelect(user.user_id);
                    setSearchTerm(user.name);
                    setShowDropdown(false);
                  }}
                  className="w-full px-4 py-2 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                >
                  <div className="font-medium text-gray-900">{user.name}</div>
                  <div className="text-xs text-gray-500">
                    ID: {user.user_id} | Consent: {user.consent_status ? '✓' : '✗'}
                  </div>
                </button>
              ))
            )}
          </div>
        )}
      </div>

      {/* Selected User Info */}
      {selectedUser && (
        <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">{selectedUser.name}</div>
              <div className="text-sm text-gray-600">
                {selectedUser.user_id} • {selectedUser.income_level || 'N/A'}
              </div>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              selectedUser.consent_status
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {selectedUser.consent_status ? 'Consent Active' : 'No Consent'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
