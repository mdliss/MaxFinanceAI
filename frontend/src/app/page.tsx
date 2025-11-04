'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

export default function Home() {
  const [apiStatus, setApiStatus] = useState<string>('Checking...')

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setApiStatus(data.status || 'online'))
      .catch(() => setApiStatus('offline'))
  }, [])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center max-w-4xl w-full">
        <h1 className="text-5xl font-bold mb-4 tracking-tight">SpendSense</h1>
        <p className="text-xl mb-12 text-[var(--text-secondary)]">Explainable Financial Education Platform</p>

        <div className="card-dark p-6 mb-12 transition-smooth">
          <div className="flex items-center justify-center gap-3">
            <div className={`w-3 h-3 rounded-full transition-smooth ${
              apiStatus === 'online' ? 'bg-green-500 animate-pulse' :
              apiStatus === 'offline' ? 'bg-red-500' :
              'bg-yellow-500'
            }`}></div>
            <p className="text-sm">
              API Status: <span className="font-semibold">{apiStatus}</span>
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link
            href="/operator"
            className="btn-accent transition-smooth block"
          >
            Operator Dashboard
          </Link>
          <Link
            href="/profile"
            className="btn-secondary transition-smooth block"
          >
            User Profile
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card-dark p-6 transition-smooth">
            <h3 className="font-semibold mb-2">Secure</h3>
            <p className="text-sm text-[var(--text-secondary)]">Bank-grade encryption for your financial data</p>
          </div>
          <div className="card-dark p-6 transition-smooth">
            <h3 className="font-semibold mb-2">Personalized</h3>
            <p className="text-sm text-[var(--text-secondary)]">AI-driven insights tailored to your behavior</p>
          </div>
          <div className="card-dark p-6 transition-smooth">
            <h3 className="font-semibold mb-2">Transparent</h3>
            <p className="text-sm text-[var(--text-secondary)]">Every recommendation comes with clear rationale</p>
          </div>
        </div>
      </div>
    </main>
  )
}
