'use client'

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const [userId, setUserId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!userId.trim()) {
      setError('Please enter a user ID');
      return;
    }

    try {
      setLoading(true);

      // Verify user exists
      const response = await fetch(`http://localhost:8000/api/v1/users/${userId}`);

      if (!response.ok) {
        throw new Error('User not found');
      }

      const user = await response.json();

      // Store user info in localStorage
      localStorage.setItem('userId', userId);
      localStorage.setItem('userName', user.name || 'User');

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-[var(--bg-primary)]">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8 drop-in-1">
          <Link href="/" className="text-3xl font-bold tracking-tight hover:text-[var(--accent-primary)] transition-smooth">
            SpendSense
          </Link>
          <p className="text-sm text-[var(--text-secondary)] mt-2">
            Sign in to view your financial dashboard
          </p>
        </div>

        {/* Login Card */}
        <div className="card-dark p-8 transition-smooth drop-in-2">
          <h2 className="text-xl font-semibold mb-6">Sign In</h2>

          <form onSubmit={handleLogin} className="space-y-6">
            {/* User ID Input */}
            <div>
              <label htmlFor="userId" className="block text-sm font-medium mb-2">
                User ID
              </label>
              <input
                type="text"
                id="userId"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="Enter your user ID (e.g., user_001)"
                className="w-full px-4 py-3 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-secondary)] transition-smooth focus:border-[var(--accent-primary)] focus:outline-none"
                disabled={loading}
              />
              <p className="text-xs text-[var(--text-secondary)] mt-2">
                Demo user IDs: test_user_1, test_user_2, user_05559915742f
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="btn-accent w-full transition-smooth py-3 font-medium"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Info */}
          <div className="mt-6 pt-6 border-t border-[var(--border-color)]">
            <p className="text-xs text-[var(--text-secondary)] text-center">
              This is a demo application. In production, this would use secure authentication.
            </p>
          </div>
        </div>

        {/* Back to Home */}
        <div className="text-center mt-6 drop-in-3">
          <Link
            href="/"
            className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent-primary)] transition-smooth"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    </main>
  );
}
