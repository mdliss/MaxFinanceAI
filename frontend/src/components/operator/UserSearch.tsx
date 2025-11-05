'use client'

import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
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
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const inputRef = useRef<HTMLInputElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    loadUsers();
  }, []);

  useEffect(() => {
    if (showDropdown && inputRef.current) {
      const rect = inputRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width,
      });
    }
  }, [showDropdown]);

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
            ref={inputRef}
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setShowDropdown(true);
            }}
            onFocus={() => setShowDropdown(true)}
            onBlur={() => {
              // Delay to allow click on dropdown items
              setTimeout(() => setShowDropdown(false), 200);
            }}
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

        {/* Dropdown - Rendered via Portal */}
        {mounted && showDropdown && searchTerm && createPortal(
          <div
            className="fixed bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg shadow-2xl max-h-60 overflow-auto dropdown-enter"
            style={{
              top: `${dropdownPosition.top + 4}px`,
              left: `${dropdownPosition.left}px`,
              width: `${dropdownPosition.width}px`,
              zIndex: 9999,
            }}
          >
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
                  onMouseDown={() => {
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
          </div>,
          document.body
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
                ? 'bg-slate-500/10 text-slate-700'
                : 'bg-red-500/10 text-red-700'
            }`}>
              {selectedUser.consent_status ? 'Consent Active' : 'No Consent'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
