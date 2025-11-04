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
    <div className="card-dark p-4 transition-smooth">
      <div className="relative">
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
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
            className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-[var(--accent-primary)] text-[var(--text-primary)] transition-smooth placeholder:text-[var(--text-muted)]"
          />
          {selectedUser && (
            <button
              onClick={() => {
                onUserSelect(null);
                setSearchTerm('');
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-smooth"
            >
              &times;
            </button>
          )}
        </div>

        {/* Dropdown */}
        {showDropdown && searchTerm && (
          <div className="absolute z-10 w-full mt-1 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg shadow-2xl max-h-60 overflow-auto dropdown-enter">
            {loading ? (
              <div className="px-4 py-3 text-sm text-[var(--text-secondary)]">Loading...</div>
            ) : error ? (
              <div className="px-4 py-3 text-sm text-red-500">{error}</div>
            ) : filteredUsers.length === 0 ? (
              <div className="px-4 py-3 text-sm text-[var(--text-secondary)]">No users found</div>
            ) : (
              filteredUsers.map((user) => (
                <button
                  key={user.user_id}
                  onClick={() => {
                    onUserSelect(user.user_id);
                    setSearchTerm(user.name);
                    setShowDropdown(false);
                  }}
                  className="w-full px-4 py-2 text-left hover:bg-[var(--bg-tertiary)] border-b border-[var(--border-color)] last:border-b-0 transition-smooth"
                >
                  <div className="font-medium">{user.name}</div>
                  <div className="text-xs text-[var(--text-muted)]">
                    ID: {user.user_id} | Consent: {user.consent_status ? 'Yes' : 'No'}
                  </div>
                </button>
              ))
            )}
          </div>
        )}
      </div>

      {/* Selected User Info */}
      {selectedUser && (
        <div className="mt-3 p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--accent-primary)] transition-smooth">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">{selectedUser.name}</div>
              <div className="text-sm text-[var(--text-secondary)]">
                {selectedUser.user_id} • {selectedUser.income_level || 'N/A'}
              </div>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-medium transition-smooth ${
              selectedUser.consent_status
                ? 'bg-green-900/30 text-green-400'
                : 'bg-red-900/30 text-red-400'
            }`}>
              {selectedUser.consent_status ? 'Consent Active' : 'No Consent'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
