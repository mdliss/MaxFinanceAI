'use client'

import { useEffect, useState, useRef } from 'react';
import { api } from '@/lib/api';

interface Alert {
  alert_id: number;
  user_id: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  is_read: boolean;
  is_dismissed: boolean;
  created_at: string;
  metadata?: any;
}

interface AlertsCenterProps {
  userId: string;
}

export default function AlertsCenter({ userId }: AlertsCenterProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchUnreadCount();
    // Refresh count every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [userId]);

  useEffect(() => {
    if (isOpen) {
      fetchAlerts();
    }
  }, [isOpen]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const fetchUnreadCount = async () => {
    try {
      const data = await api.alerts.getUnreadCount(userId);
      setUnreadCount(data.unread_count);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.alerts.getAlerts(userId);
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (alertId: number) => {
    try {
      await api.alerts.markAsRead(alertId);
      // Update local state
      setAlerts(alerts.map(a => a.alert_id === alertId ? { ...a, is_read: true } : a));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (error) {
      console.error('Error marking alert as read:', error);
    }
  };

  const handleDismiss = async (alertId: number) => {
    try {
      await api.alerts.dismissAlert(alertId);
      // Remove from local state
      setAlerts(alerts.filter(a => a.alert_id !== alertId));
      const alert = alerts.find(a => a.alert_id === alertId);
      if (alert && !alert.is_read) {
        setUnreadCount(Math.max(0, unreadCount - 1));
      }
    } catch (error) {
      console.error('Error dismissing alert:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-blue-900 bg-blue-500/10 border-blue-500/20';
      case 'high':
        return 'text-blue-800 bg-blue-400/10 border-blue-400/20';
      case 'medium':
        return 'text-blue-700 bg-blue-300/10 border-blue-300/20';
      case 'low':
        return 'text-blue-600 bg-blue-200/10 border-blue-200/20';
      default:
        return 'text-[var(--text-secondary)] bg-[var(--bg-tertiary)] border-[var(--border-color)]';
    }
  };

  const getSeverityIcon = (severity: string) => {
    const iconClass = "w-6 h-6";
    switch (severity) {
      case 'critical':
        return <svg className={iconClass} fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>;
      case 'high':
        return <svg className={iconClass} fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>;
      case 'medium':
        return <svg className={iconClass} fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" /></svg>;
      case 'low':
        return <svg className={iconClass} fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" /></svg>;
      default:
        return <svg className={iconClass} fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" /></svg>;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 hover:bg-[var(--bg-tertiary)] rounded-lg transition-smooth"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 bg-blue-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg shadow-xl z-50">
          {/* Header */}
          <div className="p-4 border-b border-[var(--border-color)]">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Notifications</h3>
              {unreadCount > 0 && (
                <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded-full font-semibold">
                  {unreadCount} new
                </span>
              )}
            </div>
          </div>

          {/* Alerts List */}
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : alerts.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-[var(--text-secondary)] text-sm">No notifications</p>
              </div>
            ) : (
              <div className="divide-y divide-[var(--border-color)]">
                {alerts.map((alert) => (
                  <div
                    key={alert.alert_id}
                    className={`p-4 hover:bg-[var(--bg-tertiary)] ${
                      !alert.is_read ? 'bg-[var(--bg-primary)]' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Severity Icon */}
                      <div className="flex-shrink-0 mt-0.5">
                        {getSeverityIcon(alert.severity)}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <h4 className="font-semibold text-sm">{alert.title}</h4>
                        </div>

                        <p className="text-sm text-[var(--text-secondary)] mb-2">
                          {alert.message}
                        </p>

                        {/* Severity Badge */}
                        <div className="flex items-center justify-between">
                          <span className={`text-xs px-2 py-1 rounded border font-medium ${getSeverityColor(alert.severity)}`}>
                            {alert.severity.toUpperCase()}
                          </span>
                          <span className="text-xs text-[var(--text-muted)]">
                            {formatDate(alert.created_at)}
                          </span>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-2 mt-3">
                          {!alert.is_read && (
                            <button
                              onClick={() => handleMarkAsRead(alert.alert_id)}
                              className="text-xs text-[var(--accent-primary)] hover:underline font-medium"
                            >
                              Mark as read
                            </button>
                          )}
                          <button
                            onClick={() => handleDismiss(alert.alert_id)}
                            className="text-xs text-[var(--text-secondary)] hover:text-red-700 hover:underline"
                          >
                            Dismiss
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {alerts.length > 0 && (
            <div className="p-3 border-t border-[var(--border-color)] text-center">
              <button
                onClick={() => {
                  setIsOpen(false);
                  // Could navigate to a full alerts page if you create one
                }}
                className="text-sm text-[var(--accent-primary)] hover:underline font-medium"
              >
                View all notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
