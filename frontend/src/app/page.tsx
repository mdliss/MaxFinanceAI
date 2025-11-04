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
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center max-w-2xl">
        <h1 className="text-4xl font-bold mb-4">SpendSense</h1>
        <p className="text-xl mb-8">Explainable Financial Education Platform</p>
        <div className="bg-gray-100 p-4 rounded mb-8">
          <p className="text-sm">API Status: <span className="font-semibold">{apiStatus}</span></p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link
            href="/operator"
            className="bg-blue-500 text-white px-6 py-4 rounded-lg hover:bg-blue-600 transition-colors font-medium"
          >
            Operator Dashboard
          </Link>
          <Link
            href="/profile"
            className="bg-green-500 text-white px-6 py-4 rounded-lg hover:bg-green-600 transition-colors font-medium"
          >
            User Profile
          </Link>
        </div>
      </div>
    </main>
  )
}
